from __future__ import annotations

import pendulum

# These imports are standard and work across Airflow 2.x and 3.x
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from collections import defaultdict


@dag(
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    doc_md="""
    ### Generación de NLU Pipeline DAG
    Este DAG permite extraer ejemplos de intentos de usuarios, 
    y los agrega a un archivo yaml según template predefinido.
    """,
    tags=["nlu", "transform", "elt"],
    dag_id="generate_nlu_pipeline",
)
def generate_nlu():
    POSTGRES_CONN_ID = "rasa_db"

    @task
    def fetch_nlu(**context):
        # Use the PostgresHook to connect to the database
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

        # Execute a query to extract data
        # get_records returns a list of tuples
        records = pg_hook.get_records(
            """
            select intent_name, example_text
            from intents
                right join training_examples using (intent_id);
        """
        )

        # Perform transformation (e.g., multiply values by 2)
        # The data must be formatted as a list of tuples for SQL insertion
        grouped = defaultdict(list)
        for intent, text in records:
            if intent is None:
                continue
            if text is None:
                continue
            grouped[intent].append(text)

        # Replace records with tuples of (intent_name, [example_texts])
        nlu_examples = [
            (intent, examples) for intent, examples in grouped.items()
        ]

        # Push the transformed data to XCom for the next task
        context["ti"].xcom_push(key="nlu_examples", value=nlu_examples)

    @task
    def fetch_regex_patterns(**context):
        # Use the PostgresHook to connect to the database
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

        # Execute a query to extract data
        # get_records returns a list of tuples
        records = pg_hook.get_records(
            """
            select entity_name, pattern from regex_patterns;
            """
        )

        # Perform transformation (e.g., multiply values by 2)
        # The data must be formatted as a list of tuples for SQL insertion
        grouped = defaultdict(list)
        for entity, pattern in records:
            if entity is None:
                continue
            if pattern is None:
                continue
            grouped[entity].append(pattern)

        # Replace records with tuples of (intent_name, [example_texts])
        regex_patterns = [
            (entity, patterns) for entity, patterns in grouped.items()
        ]

        # Push the transformed data to XCom for the next task
        context["ti"].xcom_push(key="regex_patterns", value=regex_patterns)

    @task
    def load_transformed_data(**context):
        # Retrieve nlu examples from XCom
        nlu_examples = context["ti"].xcom_pull(
            key="nlu_examples", task_ids="fetch_nlu"
        )
        regex_patterns = context["ti"].xcom_pull(
            key="regex_patterns", task_ids="fetch_regex_patterns"
        )
        # Generate the NLU YAML content
        nlu_content = "version: '3.1'\n\nnlu:\n"
        for intent, examples in nlu_examples:
            nlu_content += f"\n - intent: {intent}\n   examples: |\n"
            for example in examples:
                nlu_content += f"    - {example}\n"

        for entity, patterns in regex_patterns:
            nlu_content += f"\n - regex: {entity}\n   examples: |\n"
            for pattern in patterns:
                nlu_content += f"    - {pattern}\n"       

        # Write to a YAML file
        with open(
            "/home/icc115/caso-servicio-cliente/data/nlu.yml", "w"
        ) as f:
            f.write(nlu_content)

    # Define task dependencies
    # create_tables >> load_sample_data >> fetch_nlu() >> load_transformed_data
    fetch_nlu() >> fetch_regex_patterns() >> load_transformed_data()


# Register the DAG
generate_nlu()
