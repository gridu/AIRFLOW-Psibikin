import uuid

from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.hooks.postgres_hook import PostgresHook
from datetime import datetime
from airflow.operators.postgres_custom import PostgreSQLCountRows


def log_info(dag_id, db):
    print("{} start processing tables in database: {}".format(dag_id, db))


def push_xcom(**kwargs):
    kwargs['ti'].xcom_push(key="message", value="{} ended".format(kwargs['run_id']))


def check_table_exist(table_name):
    """ method to check that table exists """
    print("check_table_exist")
    print("TABLE NAME: " + table_name)
    hook = PostgresHook()
    # get schema name
    query = hook.get_records(sql="SELECT * FROM pg_tables;")
    for result in query:
        if 'airflow' in result:
            schema = result[0]
            print(schema)
            break

    # check table exist
    query = hook.get_first(sql="SELECT * FROM information_schema.tables "
                               "WHERE table_schema = '{}'"
                               "AND table_name = '{}';".format(schema, table_name))
    print(query)
    if query:
        return 'skip_table_creation'
    else:
        return 'create_table'


config = {
    'my_dag_id_1': {"schedule_interval": None, "start_date": datetime(2020, 2, 11), "table_name": "table_name_1"},
    'my_dag_id_2': {"schedule_interval": None, "start_date": datetime(2020, 2, 11), "table_name": "table_name_2"},
    'my_dag_id_3': {"schedule_interval": None, "start_date": datetime(2020, 2, 11), "table_name": "table_name_3"}
}

for id, args in config.items():
    with DAG(id, start_date=args["start_date"], schedule_interval=args["schedule_interval"]) as dag:
        log_info_op = PythonOperator(
            task_id="log_info_op",
            python_callable=log_info,
            op_args=[id, args["table_name"]]
        )
        user_info = BashOperator(
            task_id='user_info',
            xcom_push=True,
            bash_command='echo $USER'
        )
        branch_create_table = BranchPythonOperator(
            task_id='branch_task',
            python_callable=check_table_exist,
            op_kwargs={'table_name':args["table_name"]}
        )
        create_table = PostgresOperator(
            task_id='create_table',
            sql="CREATE TABLE {}(custom_id integer NOT NULL, user_name VARCHAR (100) NOT NULL, "
                "timestamp TIMESTAMP NOT NULL);".format(args["table_name"])
        )
        skip_create_table = DummyOperator(task_id="skip_table_creation")
        insert_row = PostgresOperator(
            task_id='insert_new_row',
            sql="INSERT INTO {} VALUES(%s, %s, %s)".format(args["table_name"]),
            trigger_rule='all_done',
            parameters=(uuid.uuid4().int % 123456789,
                        '{{ ti.xcom_pull(key="message", task_ids="push_xcom_op" }}', datetime.now())
        )
        table_query = PostgreSQLCountRows(task_id="query_the_table", table_name=args["table_name"])
        push_xcom_op = PythonOperator(
            task_id="push_xcom_op",
            provide_context=True,
            python_callable=push_xcom
        )
        log_info_op >> user_info >> branch_create_table
        branch_create_table >> create_table >> insert_row
        branch_create_table >> skip_create_table >> insert_row
        insert_row >> table_query >> push_xcom_op
        globals()[id] = dag
