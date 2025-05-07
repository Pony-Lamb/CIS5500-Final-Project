import psycopg2

try:
    # 连接数据库
    conn = psycopg2.connect(
        host="database-1.cfcenfnbcvhy.us-east-1.rds.amazonaws.com",
        database="yumlog",
        user="cis5500",
        password="kUWDP0g66ONQPkaiMKMo"
    )
    print("✅ 连接成功！")

    # 🔸 先获取游标，再执行 SQL
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM restaurants")
    row = cur.fetchone()
    print(f"数量：{row[0]}")

    # for row in rows:
    #     print(row)

    # 关闭游标和连接
    cur.close()
    conn.close()

except Exception as e:
    print("❌ 连接失败：", e)
