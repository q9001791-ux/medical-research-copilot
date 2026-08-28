from datetime import date, timedelta
import pandas as pd
from sqlalchemy import text
from db import get_engine

class QueryEngine:
    def __init__(self):
        self.engine = get_engine()

    def run(self, plan):
        if not plan.get("diagnosis_code"):
            raise ValueError("未识别疾病 / Disease not recognized.")
        endpoint = plan.get("endpoint")
        if endpoint == "OS":
            return self._survival(plan)
        if endpoint == "HBA1C_FOLLOWUP":
            return self._hba1c(plan)
        if endpoint == "BP_CONTROL":
            return self._bp(plan)
        raise ValueError("未识别可执行分析终点 / Unsupported endpoint.")

    def _where(self, plan):
        where = ["d.diagnosis_code=:code"]
        params = {"code": plan["diagnosis_code"]}
        if plan.get("years"):
            params["cutoff"] = (date.today() - timedelta(days=365 * int(plan["years"]))).isoformat()
            where.append("date(d.diagnosis_date)>=date(:cutoff)")
        return where, params

    def _age(self, df):
        if df.empty:
            return df
        df["age"] = ((pd.to_datetime(df["index_date"]) - pd.to_datetime(df["birth_date"])).dt.days / 365.25).round(1)
        return df

    def _survival(self, plan):
        where, params = self._where(plan)
        molecular_join = ""
        molecular_where = ""
        if plan.get("gene"):
            molecular_join = "JOIN molecular_tests m ON m.patient_id=d.patient_id"
            molecular_where = " AND m.gene=:gene AND m.result=:gres"
            params.update(gene=plan["gene"], gres=plan["gene_result"])
        sql = f"""
        WITH dx AS (
          SELECT d.patient_id, MIN(d.diagnosis_date) index_date
          FROM diagnoses d {molecular_join}
          WHERE {' AND '.join(where)} {molecular_where}
          GROUP BY d.patient_id
        ), tx AS (
          SELECT t.patient_id, t.regimen, MIN(t.start_date) treatment_start
          FROM treatments t JOIN dx ON dx.patient_id=t.patient_id
          WHERE date(t.start_date)>=date(dx.index_date)
          GROUP BY t.patient_id
        ), fu AS (
          SELECT patient_id, MAX(followup_date) last_followup,
                 MAX(CASE WHEN status='DEAD' THEN 1 ELSE 0 END) event
          FROM followups GROUP BY patient_id
        ), dd AS (
          SELECT patient_id, MIN(followup_date) death_date
          FROM followups WHERE status='DEAD' GROUP BY patient_id
        )
        SELECT p.patient_id,p.sex,p.birth_date,dx.index_date,tx.regimen,tx.treatment_start,
               fu.last_followup,fu.event,dd.death_date,
               (julianday(COALESCE(dd.death_date,fu.last_followup))-julianday(tx.treatment_start))/30.4375 os_months
        FROM patients p
        JOIN dx ON dx.patient_id=p.patient_id
        JOIN tx ON tx.patient_id=p.patient_id
        JOIN fu ON fu.patient_id=p.patient_id
        LEFT JOIN dd ON dd.patient_id=p.patient_id
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params=params)
        return self._age(df), sql

    def _hba1c(self, plan):
        where, params = self._where(plan)
        sql = f"""
        WITH dx AS (
          SELECT d.patient_id, MIN(d.diagnosis_date) index_date
          FROM diagnoses d WHERE {' AND '.join(where)} GROUP BY d.patient_id
        ), tx AS (
          SELECT t.patient_id,t.regimen,MIN(t.start_date) treatment_start
          FROM treatments t JOIN dx ON dx.patient_id=t.patient_id
          WHERE date(t.start_date)>=date(dx.index_date) GROUP BY t.patient_id
        ), lab AS (
          SELECT l.patient_id,l.value outcome_value,l.test_date outcome_date,
                 ROW_NUMBER() OVER(PARTITION BY l.patient_id ORDER BY date(l.test_date) DESC) rn
          FROM lab_results l JOIN tx ON tx.patient_id=l.patient_id
          WHERE l.test_code='HBA1C'
            AND date(l.test_date)>=date(tx.treatment_start,'+90 day')
            AND date(l.test_date)<=date(tx.treatment_start,'+365 day')
        )
        SELECT p.patient_id,p.sex,p.birth_date,dx.index_date,tx.regimen,tx.treatment_start,
               lab.outcome_value,lab.outcome_date
        FROM patients p
        JOIN dx ON dx.patient_id=p.patient_id
        JOIN tx ON tx.patient_id=p.patient_id
        JOIN lab ON lab.patient_id=p.patient_id AND lab.rn=1
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params=params)
        return self._age(df), sql

    def _bp(self, plan):
        where, params = self._where(plan)
        sql = f"""
        WITH dx AS (
          SELECT d.patient_id, MIN(d.diagnosis_date) index_date
          FROM diagnoses d WHERE {' AND '.join(where)} GROUP BY d.patient_id
        ), tx AS (
          SELECT t.patient_id,t.regimen,MIN(t.start_date) treatment_start
          FROM treatments t JOIN dx ON dx.patient_id=t.patient_id
          WHERE date(t.start_date)>=date(dx.index_date) GROUP BY t.patient_id
        ), bp AS (
          SELECT b.patient_id,b.sbp,b.dbp,b.observation_date,
                 ROW_NUMBER() OVER(PARTITION BY b.patient_id ORDER BY date(b.observation_date) DESC) rn
          FROM blood_pressure b JOIN tx ON tx.patient_id=b.patient_id
          WHERE date(b.observation_date)>=date(tx.treatment_start,'+30 day')
            AND date(b.observation_date)<=date(tx.treatment_start,'+365 day')
        )
        SELECT p.patient_id,p.sex,p.birth_date,dx.index_date,tx.regimen,tx.treatment_start,
               bp.sbp,bp.dbp,bp.observation_date,
               CASE WHEN bp.sbp<140 AND bp.dbp<90 THEN 1 ELSE 0 END outcome_value
        FROM patients p
        JOIN dx ON dx.patient_id=p.patient_id
        JOIN tx ON tx.patient_id=p.patient_id
        JOIN bp ON bp.patient_id=p.patient_id AND bp.rn=1
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params=params)
        return self._age(df), sql
