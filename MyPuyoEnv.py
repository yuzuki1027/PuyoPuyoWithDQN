import gym
class MyPuyoEnv(gym.Env):
   
    #metadata = {"render_modes": ["ansi", "rgb_array"], "render_fps": 4}
    def __init__(self, render_mode: Optional[str] = None):
        self.render_mode = render_mode
        """
        initで以下2つの変数を定義する必要あり
        spaces.Space型については省略します。
        
        self.action_space      : アクションが取りうる範囲を指定
        self.observation_space : 状態が取りうる範囲を指定
        """
    
    def reset():#環境のリセット　1エピソードの最初
        
    def step():#1ステップ進める
        
    def render():#描画
    
    def close():#閉じる
    
    def seed():#乱数の設定
    
        