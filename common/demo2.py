from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field
from typing import Union, Annotated, Any, Literal


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()


@app.get("/items")
# async def read_item(q: Union[str, None] = Query(default=None, max_length=50)):
async def read_item(q: Annotated[str, Query(max_length=50, min_length=3, pattern="^[A-Za-z]+$", alias="item-query", deprecated=True)]="findindex"):
    """
    Union[str, None] = Query(default=None, max_length=50) 类型声明和规则校验混在一起
    Annotated[str | None, Query(max_length=50)] = None 类型声明和规则校验分离
    使用Annotated[]="findindex"设置default值，不能使用Annotated[Query(default="findindex")]，两者有冲突
    Query(pattern="^[A-Za-z]+$", regex="" ) 设置正则表达式校验，其中regex为pydantic v1的正则表达式校验方式，pattern为pydantic v2的正则表达式校验方式，v1已弃用，推荐v2
    alias="item-query" 设置别名，FastAPI会在文档中显示该别名
    Deprecated=True 设置该参数为弃用状态，FastAPI会在文档中标记该参数为弃用
    """
    results: dict[str, Any] = {"items": [{"item_id": "Foo"},{"item_id": "Bar"}]}

    if q:
        # pylance warning:pylance根据resulets推断键值对应该为str：[], update更新的是一个字符串，所以有了错误提示，实际不影响项目运行
        # 如果result声明了类型为dict[str, Any]，则不会再有报错提示
        results.update({"q": q})
    return results

@app.post("/items/")
async def create_item(item: Item):
    """
    Create an item with the given name, description, price, and tax.
    """
    item_dict = item.model_dump()
    price_with_tax = item.price + (item.tax or 0.0)
    item_dict.update({"price_with_tax": price_with_tax})
    return item_dict

# @app.put("/items/{item_id}")
# @app.post("/items/{item_id}")
# async def update_item(item_id: int, item: Item):
#     """
#     Update an item with the given ID.
#     """
#     return {"item_id": item_id, **item.model_dump()}

@app.get("/items/{item_id}")
# async def read_item_by_id(item_id: Annotated[int, Path(title="The ID of item")], q: Annotated[str | None, Query(max_length=50)] = None):
async def read_item_by_id(*, q: str, item_id: Annotated[int, Path(title="The ID of item", ge=1, le=1000)], item: Item | None = None):
    """
    Read an item by its ID.
    带默认值的参数如果放在不带默认值的参数前，python会报错：SyntaxError: parameter without a default follows parameter with a default
    *可以用来控制参数传递方式，*之后的参数传递时必须使用q=xxx的方式传递，不能直接传递q的值
    设置校验ge=1, le=1000，表示item_id的值必须在1到1000之间,gt=1, lt=1000表示item_id的值必须在1到1000之间，不包含1和1000
    """
    restults: dict[Any, Any] = {"item_id": item_id}
    if q:
        restults.update({"q": q})
    if item:
        restults.update({"item": item})
    return restults


class FilterParams(BaseModel):
    """
    Filter parameters for items.
    Fields:元数据校验
    Literal: 限定字段值只能是指定的值
    """
    model_config = {
        "extra": "forbid",  # 禁止传递未定义的字段 
        } 
    limint: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "update_at"] = "created_at"
    tags: list[str] = []

@app.get("/itemes/about")
async def about(filter_params: Annotated[FilterParams, Query()]):
    """
    About the items endpoint.
    """
    return filter_params

class User(BaseModel):
    """
    User model with a name and an age.
    """
    name: str
    age: int = Field(..., ge=0, le=120)  # Age must be between 0 and 120

@app.post("/users/create{user_id}")
async def create_user(
    user_id: int, 
    user: User, 
    item: Item,  
    importance: Annotated[Literal["low", "medium", "high"], Body()] = "medium",  # 设置默认值为"medium"
    q: str | None = None):
    """
    Create a user with the given name and age.
    请求体中如果存在单一值，需要声明其为Body类型，不然会被默认处理为Query参数
    user_id作为路径参数，可以不声明为Path类型，FastAPI会自动将其作为路径参数处理
    q为查询参数
    """
    results = {"user": user,"item": item}
    if q:
        results.update({"q": q})
    if importance:
        results.update({"importance": importance})
    return results

@app.put("/users/{user_id}")
async def update_user(user_id: int,
    user: Annotated[User, Body(embed=True)]):
    """
    Update a user with the given ID.
    使用embed=True将item嵌入到请求体中
    """
    results = {"user_id": user_id, "user": user}
    return results

