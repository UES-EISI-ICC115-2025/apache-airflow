from __future__ import annotations

import pendulum

# These imports are standard and work across Airflow 2.x and 3.x
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from collections import defaultdict
import re


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
    RASA_CONN_ID = "rasa_db"
    CLIENTES_CONN_ID = "clientes_db"

    @task
    def fetch_nlu(**context):
        # Use the PostgresHook to connect to the database
        pg_hook = PostgresHook(postgres_conn_id=RASA_CONN_ID)

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
        nlu_examples = [(intent, examples) for intent, examples in grouped.items()]

        # Push the transformed data to XCom for the next task
        context["ti"].xcom_push(key="nlu_examples", value=nlu_examples)

    @task
    def update_productos_disponibles_intents(**context):
        # Retrieve nlu examples from XCom
        nlu_examples = context["ti"].xcom_pull(key="nlu_examples", task_ids="fetch_nlu")
        # Use the PostgresHook to connect to the database
        pg_hook = PostgresHook(postgres_conn_id=CLIENTES_CONN_ID)

        # Recupera los productos disponibles
        productos_disponibles = pg_hook.get_records(
            """
            select nombre from productos;
            """
        )
        # filtra por el intento 'choose_plan' y agrega ejemplos
        updated_nlu_examples = []
        for intent, examples in nlu_examples:
            if intent == "choose_plan":
                old_examples = examples.copy()
                examples.clear()
                for producto in productos_disponibles:
                    for old_example in old_examples:
                        # Agrega el nombre completo del producto en lugar del [placeholder]
                        intent_text = re.sub(
                                r"\[([^\]]+)\]", "[" + producto[0] + "]", old_example
                            )
                        if intent_text not in examples:
                            examples.append(
                                intent_text
                            )

                        # Adicionalmente, agrega fragmentos del nombre del producto en caso sea un nombre largo
                        # Ej: "Plan Premium Anual" -> "Plan", "Premium", "Anual"
                        nombre_producto_fragmentos = producto[0].split()
                        if len(nombre_producto_fragmentos) > 1:
                            for fragment in nombre_producto_fragmentos:
                                intent_fragment_text = re.sub(
                                    r"\[([^\]]+)\]", "[" + fragment.strip() + "]", old_example
                                )
                                if intent_fragment_text not in examples:
                                    examples.append(
                                        intent_fragment_text
                                    )
            updated_nlu_examples.append((intent, examples))

        # Push the transformed data to XCom for the next task
        context["ti"].xcom_push(key="nlu_examples", value=updated_nlu_examples)

    @task
    def fetch_regex_patterns(**context):
        # Use the PostgresHook to connect to the database
        pg_hook = PostgresHook(postgres_conn_id=RASA_CONN_ID)

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
        regex_patterns = [(entity, patterns) for entity, patterns in grouped.items()]

        # Push the transformed data to XCom for the next task
        context["ti"].xcom_push(key="regex_patterns", value=regex_patterns)

    @task
    def generar_nlu_yml(**context):
        # Retrieve nlu examples from XCom
        nlu_examples = context["ti"].xcom_pull(
            key="nlu_examples", task_ids="update_productos_disponibles_intents"
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
        with open("/home/icc115/caso-servicio-cliente/data/nlu.yml", "w") as f:
            f.write(nlu_content)

    # Define task dependencies
    # create_tables >> load_sample_data >> fetch_nlu() >> generar_nlu_yml
    (
        fetch_nlu()
        >> update_productos_disponibles_intents()
        >> generar_nlu_yml()
        << fetch_regex_patterns()
    )


# Register the DAG
generate_nlu()
