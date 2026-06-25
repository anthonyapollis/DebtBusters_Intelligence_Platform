# Databricks Notebook — Database & Schema Setup
# DebtBusters Intelligence Platform
# Run once as cluster admin before any other notebooks

# COMMAND ----------
# %run ../config/mount_config

# COMMAND ----------
# Create Unity Catalog databases (or Hive metastore if no UC)
spark.sql("CREATE DATABASE IF NOT EXISTS debtbusters_bronze COMMENT 'Raw ingested source data'")
spark.sql("CREATE DATABASE IF NOT EXISTS debtbusters_silver COMMENT 'Cleaned and validated data'")
spark.sql("CREATE DATABASE IF NOT EXISTS debtbusters_gold   COMMENT 'Star schema dimensional model'")
spark.sql("CREATE DATABASE IF NOT EXISTS debtbusters_ml     COMMENT 'ML feature tables and predictions'")

print("Databases created: bronze / silver / gold / ml")

# COMMAND ----------
# Verify
display(spark.sql("SHOW DATABASES LIKE 'debtbusters*'"))
