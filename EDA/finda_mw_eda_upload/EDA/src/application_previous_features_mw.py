"""
application_previous_features_mw.py
FinDA 담당 1 (mw) - 현재 신청(APP_) 및 과거 신청(PREV_) 피처 엔지니어링 모듈

역할분담 문서(EDA_4인_역할분담.md) 담당 1 스펙에 맞춘 재사용 함수 모음.
- 모든 데이터 경로는 저장소 루트 기준 상대경로를 사용한다 (깃허브 규칙).
- 원본 데이터는 수정/덮어쓰지 않는다. 파생 결과만 EDA/data/derived/ 에 저장한다.
- 0 이하 분모로 비율을 계산하지 않으며, 결과를 NaN 으로 두고 오류 플래그를 둔다.
- 이력이 없는 고객은 카운트 0, 금액/비율/최근값 NaN, HAS_<DOMAIN>=0 으로 구분한다.

주의(해석 경계):
- TARGET=1 은 상환곤란(payment difficulty)이며 승인 거절이 아니다.
- previous_application 의 NAME_CONTRACT_STATUS 는 과거 신청 상태일 뿐
  현재 신청의 승인 여부나 전체 거절 고객을 의미하지 않는다.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# 설정
# --------------------------------------------------------------------------- #
RANDOM_STATE = 42
DAYS_EMPLOYED_ANOMALY = 365243  # 결측 대용 특수값 (실제 근속일 아님)

# README 실측값 (검증용 상수)
EXPECTED = {
    "app_train_rows": 307511,
    "app_train_cols": 122,
    "app_test_rows": 48744,
    "prev_rows": 1670214,
    "target_pos": 24825,
}


def get_repo_root(start: Path | None = None) -> Path:
    """현재 위치에서 위로 올라가며 저장소 루트를 찾는다.

    'data' 와 'EDA' 디렉터리를 동시에 포함하는 폴더를 루트로 간주한다.
    노트북을 EDA/notebooks/ 에서 실행하든 루트에서 실행하든 동일하게 동작한다.
    """
    here = (start or Path.cwd()).resolve()
    for cand in [here, *here.parents]:
        if (cand / "data").is_dir() and (cand / "EDA").is_dir():
            return cand
    # 마커를 못 찾으면 현재 경로 반환 (루트에서 직접 실행하는 경우)
    return here


# --------------------------------------------------------------------------- #
# 공통 유틸
# --------------------------------------------------------------------------- #
def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """0 이하 분모는 계산하지 않고 NaN 으로 둔다 (무한대 방지)."""
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    out = num / den.where(den > 0)
    return out.replace([np.inf, -np.inf], np.nan)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """이항비율의 Wilson 95% 신뢰구간. n=0 이면 (nan, nan)."""
    if n == 0:
        return (np.nan, np.nan)
    phat = k / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = (z * np.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))) / denom
    return (center - margin, center + margin)


def rate_table_with_ci(df: pd.DataFrame, group_col: str,
                       target_col: str = "TARGET") -> pd.DataFrame:
    """범주/구간별 상환곤란률 + 표본수 + Wilson 95% CI 표를 만든다.

    반환 컬럼: [group_col, n, n_pos, rate, ci_low, ci_high]
    분모(n)에는 TARGET 결측이 없는 행만 사용한다.
    """
    sub = df[[group_col, target_col]].dropna(subset=[target_col])
    g = sub.groupby(group_col, observed=True)[target_col]
    out = g.agg(n="size", n_pos="sum").reset_index()
    out["rate"] = out["n_pos"] / out["n"]
    ci = out.apply(lambda r: wilson_ci(int(r["n_pos"]), int(r["n"])), axis=1)
    out["ci_low"] = [c[0] for c in ci]
    out["ci_high"] = [c[1] for c in ci]
    return out


# --------------------------------------------------------------------------- #
# APPLICATION (현재 신청) 처리
# --------------------------------------------------------------------------- #
def clean_days_employed(df: pd.DataFrame) -> pd.DataFrame:
    """DAYS_EMPLOYED 특수값(365243)을 NaN 으로 치환하고 플래그를 추가한다.

    원본 컬럼을 덮어쓰지 않도록 df 를 복사한 뒤 처리한다.
    """
    df = df.copy()
    if "DAYS_EMPLOYED" in df.columns:
        df["APP_DAYS_EMPLOYED_ANOM"] = (
            df["DAYS_EMPLOYED"] == DAYS_EMPLOYED_ANOMALY
        ).astype("int8")
        df["DAYS_EMPLOYED"] = df["DAYS_EMPLOYED"].replace(
            DAYS_EMPLOYED_ANOMALY, np.nan
        )
    return df


def add_app_features(df: pd.DataFrame) -> pd.DataFrame:
    """역할분담 문서의 APP_ 파생지표를 생성한다.

    - APP_CREDIT_INCOME_RATIO   = AMT_CREDIT / AMT_INCOME_TOTAL
    - APP_ANNUITY_INCOME_RATIO  = AMT_ANNUITY / AMT_INCOME_TOTAL  (상환부담률)
    - APP_CREDIT_GOODS_RATIO    = AMT_CREDIT / AMT_GOODS_PRICE
    - APP_AGE_YEARS             = -DAYS_BIRTH / 365.25
    - APP_EMPLOYMENT_YEARS      = -DAYS_EMPLOYED / 365.25 (특수값 제거 후)
    - EXT_SOURCE_*_MISSING      = 결측 플래그 (결측의 정보성 후보)
    - APP_EXT_SOURCE_MEAN       = 3개 외부점수 평균 (관측치 기준)
    """
    df = clean_days_employed(df)

    df["APP_CREDIT_INCOME_RATIO"] = safe_ratio(df["AMT_CREDIT"], df["AMT_INCOME_TOTAL"])
    df["APP_ANNUITY_INCOME_RATIO"] = safe_ratio(df["AMT_ANNUITY"], df["AMT_INCOME_TOTAL"])
    df["APP_CREDIT_GOODS_RATIO"] = safe_ratio(df["AMT_CREDIT"], df["AMT_GOODS_PRICE"])

    df["APP_AGE_YEARS"] = -df["DAYS_BIRTH"] / 365.25
    df["APP_EMPLOYMENT_YEARS"] = -df["DAYS_EMPLOYED"] / 365.25

    ext_cols = ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]
    present = [c for c in ext_cols if c in df.columns]
    for c in present:
        df[f"{c}_MISSING"] = df[c].isna().astype("int8")
    if present:
        df["APP_EXT_SOURCE_MEAN"] = df[present].mean(axis=1)
        df["APP_EXT_SOURCE_NA_COUNT"] = df[present].isna().sum(axis=1).astype("int8")
    return df


# --------------------------------------------------------------------------- #
# PREVIOUS APPLICATION (과거 신청) 집계
# --------------------------------------------------------------------------- #
PREV_USE_COLS = [
    "SK_ID_PREV", "SK_ID_CURR", "NAME_CONTRACT_STATUS",
    "AMT_APPLICATION", "AMT_CREDIT", "DAYS_DECISION",
]


def load_previous_chunked(prev_path: str | Path,
                          chunksize: int = 1_000_000) -> pd.DataFrame:
    """previous_application 을 청크로 읽어 필요한 컬럼만 반환한다.

    대용량 파일을 청크로 읽되 최종 통계는 전체 행 기준으로 계산한다(규칙).
    필요한 6개 컬럼만 로드하므로 메모리 부담이 작다.
    """
    parts = []
    total = 0
    for chunk in pd.read_csv(prev_path, usecols=PREV_USE_COLS, chunksize=chunksize):
        total += len(chunk)
        parts.append(chunk)
    prev = pd.concat(parts, ignore_index=True)
    assert len(prev) == total, "청크 합계와 전체 행 수 불일치"
    return prev


def aggregate_previous(prev: pd.DataFrame) -> pd.DataFrame:
    """과거 신청을 SK_ID_CURR 단위로 집계한다.

    반환 피처:
    - PREV_APPLICATION_COUNT      : 과거 신청 수
    - PREV_APPROVED_RATIO         : 승인 비율 (전체 신청 대비)
    - PREV_REFUSED_RATIO          : 거절 비율 (전체 신청 대비)
    - PREV_CANCELED_RATIO         : 취소 비율
    - PREV_RECENT_DECISION_DAYS   : 가장 최근 결정 이후 경과일(양수)
    - PREV_CREDIT_APPLICATION_RATIO: 총 실제신용액 / 총 신청액 (안전 나눗셈)

    해석 경계: NAME_CONTRACT_STATUS 는 과거 신청 상태이며 현재 승인 여부가 아니다.
    """
    prev = prev.copy()
    status = prev["NAME_CONTRACT_STATUS"]
    prev["_is_approved"] = (status == "Approved").astype("int8")
    prev["_is_refused"] = (status == "Refused").astype("int8")
    prev["_is_canceled"] = (status == "Canceled").astype("int8")

    grp = prev.groupby("SK_ID_CURR")
    agg = grp.agg(
        PREV_APPLICATION_COUNT=("SK_ID_PREV", "size"),
        _approved=("_is_approved", "sum"),
        _refused=("_is_refused", "sum"),
        _canceled=("_is_canceled", "sum"),
        _max_days_decision=("DAYS_DECISION", "max"),   # 0에 가장 가까움 = 최근
        _sum_application=("AMT_APPLICATION", "sum"),
        _sum_credit=("AMT_CREDIT", "sum"),
    )

    n = agg["PREV_APPLICATION_COUNT"]
    agg["PREV_APPROVED_RATIO"] = agg["_approved"] / n
    agg["PREV_REFUSED_RATIO"] = agg["_refused"] / n
    agg["PREV_CANCELED_RATIO"] = agg["_canceled"] / n
    # 최근 결정 이후 경과일: DAYS_DECISION 은 음수이므로 부호를 뒤집는다
    agg["PREV_RECENT_DECISION_DAYS"] = -agg["_max_days_decision"]
    # 총 신청액이 0 이하이면 비율 계산하지 않음(NaN)
    agg["PREV_CREDIT_APPLICATION_RATIO"] = safe_ratio(
        agg["_sum_credit"], agg["_sum_application"]
    )

    keep = [
        "PREV_APPLICATION_COUNT", "PREV_APPROVED_RATIO", "PREV_REFUSED_RATIO",
        "PREV_CANCELED_RATIO", "PREV_RECENT_DECISION_DAYS",
        "PREV_CREDIT_APPLICATION_RATIO",
    ]
    return agg[keep].reset_index()


# --------------------------------------------------------------------------- #
# 도메인 1 통합 산출물
# --------------------------------------------------------------------------- #
def build_domain1_features(app: pd.DataFrame,
                           prev_agg: pd.DataFrame) -> pd.DataFrame:
    """APP_ 피처 + PREV_ 집계를 SK_ID_CURR 단위로 결합한다.

    공통 인터페이스 규칙:
    - SK_ID_CURR
    - HAS_PREV : 과거 신청 이력 존재 여부(0/1)
    - APP_/PREV_ 접두사 피처
    이력 없는 고객: PREV_APPLICATION_COUNT=0, 나머지 PREV_ 는 NaN, HAS_PREV=0
    """
    out = app.merge(prev_agg, on="SK_ID_CURR", how="left")
    out["HAS_PREV"] = out["PREV_APPLICATION_COUNT"].notna().astype("int8")
    out["PREV_APPLICATION_COUNT"] = out["PREV_APPLICATION_COUNT"].fillna(0).astype("int32")
    # 이력 없는 고객의 비율/최근값은 NaN 유지 (결측과 0을 구분)
    assert out["SK_ID_CURR"].is_unique, "결합 후 SK_ID_CURR 유일성 위반"
    return out
