from databricks_deployment_helper.models import CronSchedule, PauseStatus
from databricks_deployment_helper.models import EnvironmentConfiguration, Env

BRONZE_CRON_EXPRESSION = "0 0 1 ? * *"
DATA_SERVICE_CRON_EXPRESSION = "0 0 8 ? * *"

default_data_service_schedule = CronSchedule(DATA_SERVICE_CRON_EXPRESSION, pause_status=PauseStatus.UNPAUSED)
default_bronze_schedule = EnvironmentConfiguration(
    environments_map={Env.DEV: CronSchedule(BRONZE_CRON_EXPRESSION, pause_status=PauseStatus.PAUSED)},
    default=CronSchedule(BRONZE_CRON_EXPRESSION, pause_status=PauseStatus.UNPAUSED),
)
