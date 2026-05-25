import sqlite3
import pandas as pd

conn = sqlite3.connect("/home/mdhaarith/Documents/Counsly/counsly.db")

print("--- Colleges columns ---")
colleges_df = pd.read_sql_query("SELECT * FROM colleges LIMIT 5", conn)
print(colleges_df.columns.tolist())
print(colleges_df.head(2))

print("\n--- Unique values for type, autonomous, district ---")
print("Types:", pd.read_sql_query("SELECT DISTINCT type FROM colleges", conn)["type"].tolist())
print("Autonomous:", pd.read_sql_query("SELECT DISTINCT is_autonomous FROM colleges", conn)["is_autonomous"].tolist())
print("Districts count:", pd.read_sql_query("SELECT COUNT(DISTINCT district) FROM colleges", conn).iloc[0, 0])

print("\n--- Branches columns ---")
branches_df = pd.read_sql_query("SELECT * FROM branches LIMIT 5", conn)
print(branches_df.columns.tolist())
print(branches_df.head(2))

conn.close()
