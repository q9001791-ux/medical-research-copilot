import sqlite3, random
from pathlib import Path
from datetime import date, timedelta

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "medical_demo.db"
random.seed(20260828)

def iso(d): return d.isoformat()
def clamp(x,a,b): return max(a,min(b,x))

def main():
    if DB.exists(): DB.unlink()
    con=sqlite3.connect(DB); c=con.cursor()
    c.executescript("""
    CREATE TABLE patients(patient_id TEXT PRIMARY KEY,sex TEXT,birth_date TEXT);
    CREATE TABLE diagnoses(id INTEGER PRIMARY KEY,patient_id TEXT,diagnosis_code TEXT,diagnosis_name TEXT,diagnosis_date TEXT);
    CREATE TABLE molecular_tests(id INTEGER PRIMARY KEY,patient_id TEXT,test_date TEXT,gene TEXT,variant TEXT,result TEXT);
    CREATE TABLE treatments(id INTEGER PRIMARY KEY,patient_id TEXT,regimen TEXT,start_date TEXT,end_date TEXT);
    CREATE TABLE followups(id INTEGER PRIMARY KEY,patient_id TEXT,followup_date TEXT,status TEXT);
    CREATE TABLE lab_results(id INTEGER PRIMARY KEY,patient_id TEXT,test_code TEXT,test_name TEXT,value REAL,unit TEXT,test_date TEXT);
    CREATE TABLE blood_pressure(id INTEGER PRIMARY KEY,patient_id TEXT,sbp INTEGER,dbp INTEGER,observation_date TEXT);
    """)
    today=date.today(); counter=1
    def new_patient(lo,hi):
        nonlocal counter
        pid=f"P{counter:05d}"; counter+=1
        sex=random.choice(["M","F"]); age=random.randint(lo,hi)
        birth=today-timedelta(days=int(age*365.25+random.randint(0,300)))
        c.execute("INSERT INTO patients VALUES (?,?,?)",(pid,sex,iso(birth)))
        return pid
    def cancer(n,code,name,gene,pos,regimens,ranges,positive_rate):
        for _ in range(n):
            pid=new_patient(38,84); dx=today-timedelta(days=random.randint(40,1700))
            c.execute("INSERT INTO diagnoses(patient_id,diagnosis_code,diagnosis_name,diagnosis_date) VALUES (?,?,?,?)",(pid,code,name,iso(dx)))
            positive=random.random()<positive_rate
            result=pos if positive else ("WT" if pos=="MUT" else "NEG")
            c.execute("INSERT INTO molecular_tests(patient_id,test_date,gene,variant,result) VALUES (?,?,?,?,?)",(pid,iso(dx+timedelta(days=random.randint(1,20))),gene,"Variant" if positive else "Negative/WT",result))
            tx=dx+timedelta(days=random.randint(8,35)); regimen=random.choice(regimens)
            c.execute("INSERT INTO treatments(patient_id,regimen,start_date,end_date) VALUES (?,?,?,?)",(pid,regimen,iso(tx),iso(tx+timedelta(days=365))))
            lo,hi=ranges[regimen]
            death=tx+timedelta(days=random.randint(lo,hi)); censor=min(today,tx+timedelta(days=random.randint(260,1250)))
            if death<=today and death<=censor:
                c.execute("INSERT INTO followups(patient_id,followup_date,status) VALUES (?,?,?)",(pid,iso(death),"DEAD"))
            else:
                fu=censor if censor>tx else tx+timedelta(days=90)
                c.execute("INSERT INTO followups(patient_id,followup_date,status) VALUES (?,?,?)",(pid,iso(fu),"ALIVE"))
    cancer(650,"C34-NSCLC","NSCLC","EGFR","MUT",["EGFR-TKI","Chemo","IO+Chemo"],{"EGFR-TKI":(520,1450),"Chemo":(280,900),"IO+Chemo":(390,1150)},.68)
    cancer(580,"C50-BREAST","Breast cancer","HER2","POS",["Trastuzumab+Chemo","Chemo","T-DM1"],{"Trastuzumab+Chemo":(650,1600),"Chemo":(340,1000),"T-DM1":(520,1350)},.45)
    cancer(560,"C18-CRC","Colorectal cancer","KRAS","MUT",["FOLFOX","FOLFIRI","FOLFOX+Bevacizumab"],{"FOLFOX":(430,1150),"FOLFIRI":(380,1050),"FOLFOX+Bevacizumab":(540,1350)},.48)
    diabetes_effect={"Metformin":-.7,"SGLT2i":-1.0,"GLP-1RA":-1.45}
    for _ in range(720):
        pid=new_patient(35,79); dx=today-timedelta(days=random.randint(40,1700)); regimen=random.choice(list(diabetes_effect)); tx=dx+timedelta(days=random.randint(1,28))
        c.execute("INSERT INTO diagnoses(patient_id,diagnosis_code,diagnosis_name,diagnosis_date) VALUES (?,?,?,?)",(pid,"E11-T2DM","Type 2 diabetes",iso(dx)))
        c.execute("INSERT INTO treatments(patient_id,regimen,start_date,end_date) VALUES (?,?,?,?)",(pid,regimen,iso(tx),iso(tx+timedelta(days=365))))
        baseline=clamp(random.gauss(8.6,1.1),6.6,13); follow=clamp(baseline+diabetes_effect[regimen]+random.gauss(0,.55),5.5,12.5)
        c.execute("INSERT INTO lab_results(patient_id,test_code,test_name,value,unit,test_date) VALUES (?,?,?,?,?,?)",(pid,"HBA1C","HbA1c",round(baseline,2),"%",iso(tx-timedelta(days=10))))
        c.execute("INSERT INTO lab_results(patient_id,test_code,test_name,value,unit,test_date) VALUES (?,?,?,?,?,?)",(pid,"HBA1C","HbA1c",round(follow,2),"%",iso(tx+timedelta(days=random.randint(120,300)))))
    htn_effect={"ACEI/ARB":(-12,-6),"CCB":(-14,-7),"ACEI/ARB+CCB":(-22,-12)}
    for _ in range(720):
        pid=new_patient(40,84); dx=today-timedelta(days=random.randint(40,1700)); regimen=random.choice(list(htn_effect)); tx=dx+timedelta(days=random.randint(1,24))
        c.execute("INSERT INTO diagnoses(patient_id,diagnosis_code,diagnosis_name,diagnosis_date) VALUES (?,?,?,?)",(pid,"I10-HTN","Hypertension",iso(dx)))
        c.execute("INSERT INTO treatments(patient_id,regimen,start_date,end_date) VALUES (?,?,?,?)",(pid,regimen,iso(tx),iso(tx+timedelta(days=365))))
        sbp0=random.randint(145,178); dbp0=random.randint(88,108); es,ed=htn_effect[regimen]
        sbp=int(clamp(sbp0+random.gauss(es,7),105,190)); dbp=int(clamp(dbp0+random.gauss(ed,5),65,115))
        c.execute("INSERT INTO blood_pressure(patient_id,sbp,dbp,observation_date) VALUES (?,?,?,?)",(pid,sbp0,dbp0,iso(tx-timedelta(days=7))))
        c.execute("INSERT INTO blood_pressure(patient_id,sbp,dbp,observation_date) VALUES (?,?,?,?)",(pid,sbp,dbp,iso(tx+timedelta(days=random.randint(60,260)))))
    con.commit(); con.close()
    print(f"Expanded demo DB generated: {DB}")
    print(f"Total synthetic patients: {counter-1}")
if __name__=="__main__": main()
