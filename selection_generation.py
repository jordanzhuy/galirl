from openai import AsyncOpenAI
import os

deleted = """在回答之前：请考虑以下所有的因素，以下使用-进行标注的条件为每次开始生成选项前必须考虑
-对方的昵称，关系，以及对话内容（例：我：...,对方：...）"""

startup_prompt = """你是一名galgame的男主、女主，跟你对话的是你的攻略对象，你现在只能够用galgame中三种对话选项的方式来回答我的问题
不需要任何背景细节
说话方式应当与攻略对象的语气相符，如对方用幽默诙谐的语气，你也应当放松你的语气，如果对方使用认真的的语气与你互动，你也应当用认真的语气和对方互动。
回答应当保持日常，不要过度书面化，不要像小说里的男主一样，用非常油腻的方式（特指过度对对方温柔，无条件宠溺对方）回答问题
对话时的回答应与对方字数相当，且不要表现出过度的关心或是过度的在意
男主的存在应让玩家感到“如果是我，也会这样选择”，同时通过他的视角体验到超越现实的理想化情感联结
做出的回答应当与网络聊天的环境符合，不要做出与对方有物理意义上互动的行为（如：递奶茶，凑近等等）
（8普适 + 2独特）
+ 性格深度（温柔≠懦弱，行动力≠莽撞）
普适性设定
隐藏的独特性（这点应当非常非常少，不要在日常聊天中混入例如突然带对方去某处游玩的场景，约会是胜利的号角，不是冲锋的信号）
例如：细腻的观察力 特殊爱好或技能 矛盾性 
性格 共情能力 适度的主动性 幽默与真诚并存
雷区：过度工具化，性格单一/扁平化，逻辑断裂，
主动拒绝不合理请求、注意细节。
除第一次输入以外，用户每次的输入将会为 “用户选择了：具体内容 && 对方说：具体内容”。第一次输入为：“对方说：具体内容”。
注意，用户的（具体对话内容）可能与选项略有不同，请遵从用户的具体内容和对方的具体内容，以及所有的上下文进行选项的生成。
回答的格式固定为：“
选项一内容
||
选项二内容
||
选项三内容
”
且无任何附加描述。内容之前无需任何序号或者制表符。"""

def _make_prompt(other_response, user_selection=None):
    args = {"user": user_selection, "other": other_response}
    if not user_selection: # first conversation with no selection
        return "对方说：{other}".format(**args)
    else:
        return "用户选择了：{user} && 对方说：{other}".format(**args)


class DialogueSession:
    def __init__(self):
        api_key = os.environ.get("DEESEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEESEEK_API_KEY env-var not set")
        self.client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.dialogues = []

    def init_session(self):
        self.dialogues = []
        self.dialogues.append({"role": "system", "content": startup_prompt})



    async def generate_choice(self, other_response, user_selection=None):
        self.dialogues.append({"role": "user", 
                               "content": _make_prompt(other_response, user_selection)})
        # print("current dialogue: ", self.dialogues)
        response = await self.client.chat.completions.create(
            model="deepseek-chat",
            messages=self.dialogues,
            stream=False
        )
        self.dialogues.append(response.choices[0].message)
        selections = response.choices[0].message.content.split("||")
        selections = {idx: s.strip() for idx, s in enumerate(selections)}
        return selections 

