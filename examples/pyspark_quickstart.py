"""PySpark quickstart for PipeDoctor.

Run this in a local Spark environment, Databricks notebook, or VSCode notebook.
"""

from pyspark.sql import SparkSession, functions as F

from pipedoctor import diagnose


spark = SparkSession.builder.appName("pipedoctor-pyspark-demo").getOrCreate()

orders = spark.sql(
    """
    SELECT * FROM VALUES
      (1, 101, 1001, '2026-05-01', 2, 120.0),
      (2, 102, 1002, '2026-05-01', 1, 75.0),
      (3, 101, 1003, '2026-05-02', 4, 240.0),
      (4, 103, 1001, '2026-05-02', 1, 60.0),
      (5, 104, 1002, '2026-05-03', 3, 225.0),
      (6, 105, 1004, '2026-05-03', 2, 180.0)
    AS orders(order_id, customer_id, product_id, order_date, quantity, amount)
    """
)

customers = spark.sql(
    """
    SELECT * FROM VALUES
      (101, 'Ravi', 'US'),
      (102, 'Anu', 'India'),
      (103, 'John', 'UK'),
      (104, 'Meera', 'India'),
      (105, 'Sara', 'US')
    AS customers(customer_id, customer_name, country)
    """
)

sales_report_df = (
    orders.join(customers, "customer_id")
    .withColumn("order_date", F.to_date("order_date"))
    .groupBy("country")
    .agg(F.countDistinct("order_id").alias("orders"), F.sum("amount").alias("revenue"))
    .repartition(4, "country")
    .orderBy(F.desc("revenue"))
)

diagnose(sales_report_df, name="country_sales", key_columns=["country"], sample_rows=10000)
