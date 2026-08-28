import io, base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


def _image(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=155, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def _km_curve(times, events):
    times = np.asarray(times, dtype=float)
    events = np.asarray(events, dtype=int)
    event_times = np.sort(np.unique(times[events == 1]))
    xs = [0.0]
    ys = [1.0]
    surv = 1.0
    for t in event_times:
        at_risk = np.sum(times >= t)
        deaths = np.sum((times == t) & (events == 1))
        if at_risk > 0:
            surv *= (1.0 - deaths / at_risk)
        xs.append(float(t))
        ys.append(float(surv))
    end = float(np.max(times)) if len(times) else 0.0
    if not xs or xs[-1] < end:
        xs.append(end)
        ys.append(surv)
    median = None
    for x, y in zip(xs, ys):
        if y <= 0.5:
            median = x
            break
    return np.asarray(xs), np.asarray(ys), median


def _multigroup_logrank(times, events, groups):
    times = np.asarray(times, dtype=float)
    events = np.asarray(events, dtype=int)
    groups = np.asarray(groups)
    labels = np.array(sorted(pd.unique(groups)))
    k = len(labels)
    observed = np.zeros(k)
    expected = np.zeros(k)
    cov = np.zeros((k, k))
    for t in np.sort(np.unique(times[events == 1])):
        risk = times >= t
        deaths_mask = (times == t) & (events == 1)
        n = risk.sum()
        d = deaths_mask.sum()
        if n <= 1 or d == 0:
            continue
        n_g = np.array([np.sum(risk & (groups == g)) for g in labels], dtype=float)
        d_g = np.array([np.sum(deaths_mask & (groups == g)) for g in labels], dtype=float)
        p = n_g / n
        observed += d_g
        expected += d * p
        factor = d * (n - d) / (n - 1)
        cov += factor * (np.diag(p) - np.outer(p, p))
    diff = observed - expected
    if k <= 1:
        return 0.0, 1.0
    v = cov[:-1, :-1]
    z = diff[:-1]
    try:
        chi2 = float(z.T @ np.linalg.pinv(v) @ z)
        pvalue = float(stats.chi2.sf(chi2, k - 1))
    except Exception:
        chi2, pvalue = 0.0, 1.0
    return chi2, pvalue


class StatsEngine:
    def analyze(self, df, plan, lang="zh"):
        kind = plan["endpoint_type"]
        if kind == "survival":
            return self.survival(df, lang)
        if kind == "continuous":
            return self.continuous(df, lang)
        if kind == "categorical":
            return self.categorical(df, lang)
        return {"error": "Unsupported endpoint type."}

    def survival(self, df, lang):
        d = df.drop_duplicates("patient_id").dropna(subset=["regimen", "os_months"]).copy()
        d = d[d.os_months >= 0]
        d["event"] = d.event.fillna(0).astype(int)
        groups = sorted(d.regimen.unique())
        fig, ax = plt.subplots(figsize=(8.4, 5))
        summary = []
        for group in groups:
            sub = d[d.regimen == group]
            x, y, median = _km_curve(sub.os_months.values, sub.event.values)
            ax.step(x, y, where="post", label=group)
            summary.append({
                "group": group,
                "n": len(sub),
                "events": int(sub.event.sum()),
                "median_os_months": None if median is None else round(float(median), 2),
            })
        ax.set(title="Kaplan-Meier Overall Survival", xlabel="Months", ylabel="Survival probability")
        ax.set_ylim(0, 1.03)
        ax.legend()
        ax.grid(alpha=.2)
        fig.tight_layout()
        _, p = _multigroup_logrank(d.os_months.values, d.event.values, d.regimen.values)

        cox = []
        try:
            from statsmodels.duration.hazard_regression import PHReg
            cdf = d[["os_months", "event", "age", "sex", "regimen"]].dropna().copy()
            cdf["sex_male"] = (cdf.sex == "M").astype(int)
            xdf = pd.get_dummies(cdf[["age", "sex_male", "regimen"]], columns=["regimen"], drop_first=True, dtype=float)
            model = PHReg(cdf["os_months"].astype(float).values, xdf.astype(float).values, status=cdf["event"].astype(int).values, ties="breslow")
            result = model.fit(disp=0)
            ci = np.asarray(result.conf_int())
            pvals = np.asarray(result.pvalues)
            params = np.asarray(result.params)
            for i, name in enumerate(xdf.columns):
                cox.append({
                    "variable": str(name),
                    "HR": round(float(np.exp(params[i])), 3),
                    "CI95_low": round(float(np.exp(ci[i, 0])), 3),
                    "CI95_high": round(float(np.exp(ci[i, 1])), 3),
                    "p": float(pvals[i]),
                })
        except Exception:
            pass

        if lang == "en":
            conclusion = f"Survival curves {'differed significantly' if p < .05 else 'did not differ significantly'} across regimens (Log-rank P={p:.4g})."
        else:
            conclusion = f"不同治疗方案的生存曲线{'存在' if p < .05 else '未发现'}统计学显著差异（Log-rank P={p:.4g}）。"
        return {"method": "Kaplan-Meier + Log-rank + Cox PH", "p": p, "summary": summary, "cox": cox, "image": _image(fig), "conclusion": conclusion}

    def continuous(self, df, lang):
        d = df.dropna(subset=["regimen", "outcome_value"]).copy()
        groups = sorted(d.regimen.unique())
        arrays = [d[d.regimen == g].outcome_value.astype(float).values for g in groups]
        if all(len(a) >= 30 for a in arrays):
            result = stats.f_oneway(*arrays)
            method = "One-way ANOVA"
        else:
            result = stats.kruskal(*arrays)
            method = "Kruskal-Wallis"
        p = float(result.pvalue)
        summary = [{"group": g, "n": len(a), "mean": round(float(np.mean(a)), 2), "sd": round(float(np.std(a, ddof=1)), 2), "median": round(float(np.median(a)), 2)} for g, a in zip(groups, arrays)]
        fig, ax = plt.subplots(figsize=(8.4, 5))
        ax.boxplot(arrays, tick_labels=groups, showmeans=True)
        ax.set(title="Follow-up HbA1c by Regimen", ylabel="HbA1c (%)")
        ax.tick_params(axis="x", rotation=12)
        fig.tight_layout()
        if lang == "en":
            conclusion = f"Follow-up HbA1c {'differed significantly' if p < .05 else 'did not differ significantly'} across regimens ({method}, P={p:.4g})."
        else:
            conclusion = f"不同治疗方案的随访HbA1c水平{'存在' if p < .05 else '未发现'}统计学显著差异（{method}，P={p:.4g}）。"
        return {"method": method, "p": p, "summary": summary, "image": _image(fig), "conclusion": conclusion}

    def categorical(self, df, lang):
        d = df.dropna(subset=["regimen", "outcome_value"]).copy()
        d["outcome_value"] = d.outcome_value.astype(int)
        table = pd.crosstab(d.regimen, d.outcome_value)
        _, p, _, _ = stats.chi2_contingency(table)
        p = float(p)
        summary = []
        for group in table.index:
            total = int(table.loc[group].sum())
            controlled = int(table.loc[group].get(1, 0))
            summary.append({"group": group, "n": total, "controlled": controlled, "control_rate_pct": round(100 * controlled / total, 1)})
        fig, ax = plt.subplots(figsize=(8.4, 5))
        ax.bar([x["group"] for x in summary], [x["control_rate_pct"] for x in summary])
        ax.set(title="Blood Pressure Control Rate by Regimen", ylabel="Control rate (%)")
        ax.set_ylim(0, 100)
        ax.tick_params(axis="x", rotation=12)
        fig.tight_layout()
        if lang == "en":
            conclusion = f"Blood-pressure control rates {'differed significantly' if p < .05 else 'did not differ significantly'} across regimens (Chi-square, P={p:.4g})."
        else:
            conclusion = f"不同治疗方案的血压控制率{'存在' if p < .05 else '未发现'}统计学显著差异（卡方检验，P={p:.4g}）。"
        return {"method": "Chi-square test", "p": p, "summary": summary, "image": _image(fig), "conclusion": conclusion}
