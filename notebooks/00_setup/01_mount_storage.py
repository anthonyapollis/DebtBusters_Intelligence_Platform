# Databricks Notebook — Mount Azure Data Lake Storage Gen2
# DebtBusters Intelligence Platform
# Run once with a service principal that has Storage Blob Data Contributor

# COMMAND ----------
# Widgets — override in job parameters
dbutils.widgets.text("storage_account", "debtbusterssa")
dbutils.widgets.text("container",       "debtbusters")
dbutils.widgets.text("tenant_id",       "")
dbutils.widgets.text("client_id",       "")
dbutils.widgets.text("client_secret",   "")   # store in Databricks secret scope in production

STORAGE_ACCOUNT = dbutils.widgets.get("storage_account")
CONTAINER       = dbutils.widgets.get("container")
TENANT_ID       = dbutils.widgets.get("tenant_id")
CLIENT_ID       = dbutils.widgets.get("client_id")
CLIENT_SECRET   = dbutils.widgets.get("client_secret")

# COMMAND ----------
MOUNT_POINT = "/mnt/debtbusters"

configs = {
    "fs.azure.account.auth.type":                f"OAuth",
    "fs.azure.account.oauth.provider.type":      f"org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
    "fs.azure.account.oauth2.client.id":         CLIENT_ID,
    "fs.azure.account.oauth2.client.secret":     CLIENT_SECRET,
    "fs.azure.account.oauth2.client.endpoint":   f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token",
}

if any(m.mountPoint == MOUNT_POINT for m in dbutils.fs.mounts()):
    print(f"{MOUNT_POINT} already mounted — skipping.")
else:
    dbutils.fs.mount(
        source=f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/",
        mount_point=MOUNT_POINT,
        extra_configs=configs,
    )
    print(f"Mounted {MOUNT_POINT} successfully.")

# COMMAND ----------
# Create folder structure
for folder in ["raw", "bronze", "silver", "gold", "ml", "checkpoints", "archive"]:
    dbutils.fs.mkdirs(f"{MOUNT_POINT}/{folder}")

display(dbutils.fs.ls(MOUNT_POINT))
