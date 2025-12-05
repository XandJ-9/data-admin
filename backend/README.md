# 项目介绍


# 快速开始
## 环境准备
- 使用uv安装
```bash
uv sync
```
uv工具会自动创建虚拟环境（默认再当前目录下.venv）

或者手动创建虚拟环境
```bash
python -m venv .venv
```
激活虚拟环境
```bash
source .venv/bin/activate
```
- 使用pip安装
```bash
pip install -r requirements.txt
```

## 数库迁移
- 初始化数据库
```bash
python manage.py migrate
```
- 创建超级用户
```bash
python manage.py createsuperuser
```
