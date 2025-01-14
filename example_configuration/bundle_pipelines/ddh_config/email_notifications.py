from databricks_deployment_helper.models import EnvironmentConfiguration, Env, EmailNotification

default_email_notifications = EnvironmentConfiguration(
    {
        Env.STG: EmailNotification(on_failure=["stg@example.com"]),
        Env.PRE: EmailNotification(on_failure=["pre@example.com"]),
        Env.PRD: EmailNotification(on_failure=["prd@example.com"]),
    }
)
