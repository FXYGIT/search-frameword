# proxy_pool/models.py
import time
from pydantic import BaseModel, Field

class Proxy(BaseModel):
    proxy_str: str = Field(..., description="带认证的完整代理 URL")
    created_at: float = Field(default_factory=time.time, description="UNIX 时间戳，记录获取时刻")
    use_count: int = Field(0, description="累计被分配给请求的次数")

    @property
    def age(self) -> float:
        return time.time() - self.created_at

    @property
    def ttl_left(self) -> float:
        return max(0.0, 60.0 - self.age)