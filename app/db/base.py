from sqlalchemy.orm import declarative_base

# 声明式基类：所有 ORM 模型继承它。
# 独立放在 db/base.py，避免 database.py（引擎/会话）与模型耦合循环导入。
Base = declarative_base()
