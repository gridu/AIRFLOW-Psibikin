from airflow import DAG
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from airflow.operators.subdag_operator import SubDagOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor

path = Variable.get('name_path_variable', default_var="/tmp")
file_name = Variable.get('name_file_variable', default_var="run")
file_path = '{0}/{1}'.format(path, file_name)
dag_name = "sensor_trigger_dag_id"
external_dag_name = "my_dag_id_1"

def pull_xcom(**kwargs):
    message = kwargs['ti'].xcom_pull(key="message", task_ids='push_xcom_op', dag_id=external_dag_name)
    print(message)
    print(kwargs)

def create_subdag(parent_dag_name, child_dag_name):
    subdag = DAG(
        dag_id='{0}.{1}'.format(parent_dag_name, child_dag_name),
        # schedule_interval="@once",
        schedule_interval=None,
        start_date=datetime(2020, 2, 11)
    )
    ext_dag_sensor = ExternalTaskSensor(
        task_id="ext_dag_sensor",
        external_dag_id=external_dag_name,
        external_task_id=None,
        poke_interval=20,
        dag=subdag
    )
    remove_file = BashOperator(
        task_id="remove_file_id",
        bash_command=f'rm {file_path}',
        dag=subdag
    )
    create_ts_file = BashOperator(
        task_id="create_ts_file_id",
        bash_command=f'touch {path}/finished_{{{{ ts_nodash }}}}',
        dag=subdag
    )
    pull_xcom_op = PythonOperator(
        task_id="pull_xcom_op",
        provide_context=True,
        python_callable=pull_xcom,
        dag=subdag
    )
    ext_dag_sensor >> pull_xcom_op >> remove_file >> create_ts_file
    return subdag


with DAG(dag_name, start_date=datetime(2020, 2, 11), schedule_interval=None) as dag:
    sensor = FileSensor(
        task_id="file_sensor_task_id",
        filepath=file_path,
        poke_interval=30,
        fs_conn_id="fs_default"
    )
    trigger_op = TriggerDagRunOperator(
        task_id="trigger_my_dag_id",
        trigger_dag_id=external_dag_name,
        execution_date='{{ execution_date }}'
    )
    sub_dag = SubDagOperator(
        subdag=create_subdag(dag_name, 'process_result_subdag'),
        task_id='process_result_subdag',
        dag=dag
    )
    sensor >> trigger_op >> sub_dag
