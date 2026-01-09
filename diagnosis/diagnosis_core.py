from typing import Dict, Literal, TypedDict


ThinkingType = Literal["side_job", "career_shift", "hybrid", "undifferentiated"]
StopLevel = Literal["low", "medium", "high"]


class DiagnosisResult(TypedDict):
    a_score: int
    b_score: int
    c_score: int
    d_score: int
    thinking_type: ThinkingType
    stop_level: StopLevel
    thinking_type_label: str
    stop_level_label: str
    summary_label: str


def diagnose_thinking_pattern(answers: Dict[int, int]) -> DiagnosisResult:
    """
    医療職の思考タイプを判定するコアロジック。
    answers: {1:1, 2:0, ...} の形式
    """

    # 欠損を0で補完
    def get(q_num: int) -> int:
        v = answers.get(q_num, 0)
        return 1 if v == 1 else 0

    # --- スコア計算 ---
    a_score = sum(get(q) for q in range(1, 6))     # A：現状限界
    b_score = sum(get(q) for q in range(6, 11))    # B：思考停止
    c_score = sum(get(q) for q in range(11, 16))   # C：副業志向
    d_score = sum(get(q) for q in range(16, 21))   # D：転職志向

    # --- 思考タイプ判定（優先順位つき） ---
    if c_score >= 3 and d_score >= 3:
        thinking_type = "hybrid"
        thinking_type_label = "ハイブリッド思考"

    elif c_score >= 3 and d_score <= 2:
        thinking_type = "side_job"
        thinking_type_label = "副業思考"

    elif d_score >= 3 and c_score <= 2:
        thinking_type = "career_shift"
        thinking_type_label = "転職思考"

    elif c_score <= 2 and d_score <= 2 and a_score >= 3:
        thinking_type = "undifferentiated"
        thinking_type_label = "未分化思考"

    else:
        thinking_type = "hybrid"
        thinking_type_label = "ハイブリッド思考（揺れあり）"

    # --- 思考停止レベル ---
    if b_score <= 1:
        stop_level = "low"
        stop_level_label = "思考停止レベル：低"
    elif 2 <= b_score <= 3:
        stop_level = "medium"
        stop_level_label = "思考停止レベル：中"
    else:
        stop_level = "high"
        stop_level_label = "思考停止レベル：高"

    summary_label = f"{thinking_type_label} × {stop_level_label}"

    return DiagnosisResult(
        a_score=a_score,
        b_score=b_score,
        c_score=c_score,
        d_score=d_score,
        thinking_type=thinking_type,
        stop_level=stop_level,
        thinking_type_label=thinking_type_label,
        stop_level_label=stop_level_label,
        summary_label=summary_label,
    )
