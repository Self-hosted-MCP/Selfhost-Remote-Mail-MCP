"""Says hello: the smallest possible add-on, to copy when you start a new one."""


def setup(api):
    greeting = api.setting("HELLO_GREETING", "Hello")

    @api.tool(api.READ)
    def hello(name: str = "there") -> str:
        """Say hello to someone. Changes nothing."""
        return f"{greeting}, {name}!"
