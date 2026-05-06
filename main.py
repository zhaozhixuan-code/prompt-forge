from app.main import app


def main() -> None:
    # 兼容直接运行 python main.py 的启动方式。
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8123, reload=True)


if __name__ == "__main__":
    main()
