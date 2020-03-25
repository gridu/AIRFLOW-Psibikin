from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
from airflow.hooks.postgres_hook import PostgresHook
import logging


log = logging.getLogger(__name__)


class PostgreSQLCountRows(BaseOperator):
    """ operator to check table exist"""

    @apply_defaults
    def __init__(self, table_name,
                 *args, **kwargs):
        """

        :param table_name: table name
        """
        self.table_name = table_name
        self.hook = PostgresHook()
        super(PostgreSQLCountRows, self).__init__(*args, **kwargs)

    def execute(self, context):

        result = self.hook.get_first(
            sql="SELECT COUNT(*) FROM {};".format(self.table_name))
        log.info("Result: {}".format(result))
        return result


class PostgreSQLCustomOperatorsPlugin(AirflowPlugin):
    name = "postgres_custom"
    operators = [PostgreSQLCountRows]