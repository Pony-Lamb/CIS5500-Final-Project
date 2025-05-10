import psycopg2

try:
    # 连接数据库
    conn = psycopg2.connect(
        host="database-1.cfcenfnbcvhy.us-east-1.rds.amazonaws.com",
        database="yumlog",
        user="cis5500",
        password="kUWDP0g66ONQPkaiMKMo"
    )
    print("✅ connected！")

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM restaurants")
    row = cur.fetchone()
    print(f"count: {row[0]}")

    # for row in rows:
    #     print(row)

    cur.close()
    conn.close()

except Exception as e:
    print("❌ connection failed: ", e)
