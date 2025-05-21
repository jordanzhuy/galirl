import time

class MockSession():
    def __init__(self):
        self.idx = 0

    def init_session(self):
        self.mock_selections = [
            {0: '1', 1: '2', 2: '3'},
            {0: '11', 1: '22', 2: '33'},
            {0: '行啊，不过你得等我冲个澡，打完球一身汗', 1: '现在跑过去估计能赶上最后一波，冲！', 2: '那我得多点一份叉烧，运动完特别想吃肉'},
            {0: '好好好，我跑着去，给我留个位子啊', 1: '那要不你先帮我点一份？我五分钟就到', 2: '这么急？那我不洗了，直接去吧'}
        ]
    
    async def generate_choice(self, other, user):
        self.idx += 1
        time.sleep(1)
        return self.mock_selections[self.idx]