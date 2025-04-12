def get_level_from_score(score: int) -> int:
    """
    예시 규칙:
      0~100 => level 1
      101~200 => level 2
      201~300 => level 3
      301~400 => level 4
      401 이상 => level 5
    """
    if score <= 100:
        return 1
    elif score <= 200:
        return 2
    elif score <= 300:
        return 3
    elif score <= 400:
        return 4
    else:
        return 5
