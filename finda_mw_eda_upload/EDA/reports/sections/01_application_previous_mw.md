# 담당 1 EDA 리포트 — 현재 신청(APP) 및 과거 신청(PREV)

**작업자:** mw
**원천 데이터:** `application_train.csv`(307,511×122), `application_test.csv`(48,744×121), `previous_application.csv`(1,670,214×37)
**산출물:** `EDA/data/derived/app_prev_features_mw.parquet` (SK_ID_CURR 단위, 307,511행 × 17열)
**노트북:** `EDA/notebooks/01_application_previous_eda_mw.ipynb` (커널 재시작 후 처음부터 끝까지 실행 검증 완료)

> **해석 경계** — `TARGET=1`은 상환곤란(payment difficulty)이며 승인 거절이 아니다. 아래 결과는 관측 상관관계이며 인과가 아니고, 승인 컷오프·구제율은 이 단계에서 주장하지 않는다. `previous_application.NAME_CONTRACT_STATUS`는 과거 신청 상태일 뿐 현재 심사 결과가 아니다.

## 1. 데이터 검증
README 실측값과 코드 대조 결과 전부 일치했다. train 307,511행, TARGET=1 24,825건(8.07%), train/test `SK_ID_CURR` 중복 0건, `SK_ID_CURR` 유일성 확보. `DAYS_EMPLOYED=365243` 특수값 55,374건은 플래그 생성 후 `NaN`으로 분리했다. (노트북 표 1)

## 2. 핵심 표·그래프

| # | 산출물 | 내용 |
|---|---|---|
| 그림 1 | `fig01_target_balance_mw.png` | 타깃 클래스 불균형 (8.07%) |
| 그림 2 | `fig02_annuity_income_ratio_vs_default_mw.png` | 상환부담률 구간별 곤란률 + Wilson CI |
| 그림 3 | `fig03_credit_income_ratio_vs_default_mw.png` | 소득대비신용액 구간별 (비단조) |
| 그림 4 | `fig04_ext_source_mean_vs_default_mw.png` | 외부점수평균 구간별 (압도적 신호) |
| 그림 5 | `fig05_ext_source_missing_vs_default_mw.png` | 외부점수 결측 플래그의 정보성 |
| 그림 6 | `fig06_prev_refused_ratio_vs_default_mw.png` | 과거 거절비율 구간별 (강한 단조) |
| 그림 7 | `fig07_train_test_distribution_mw.png` | train/test 분포 비교 |
| 그림 8 | `fig08_categorical_rate_mw.png` | 성별·학력·소득·가족·주거 범주별 곤란률 (분석질문①) |

이 외에 데이터 품질 표(자료형 분포, 상대 날짜 방향 검증, 전 변수 결측률 스캔, train/test 이력 보유율 비교)를 포함한다.
모든 비율에는 표본수(분모)와 Wilson 95% 신뢰구간을 병기했고, 표본 500건/1% 미만 범주는 `OTHER`로 묶되 원본은 표에 보존했다.

## 3. 근거 기반 결론

1. **외부 신용점수(EXT_SOURCE)가 압도적 단일 신호다.** 점수평균 하위구간(<0.2) 상환곤란률 **28.2%** vs 상위구간(>0.8) **1.7%**로 약 16배 차이이며 Wilson CI가 비중첩이다. 결측 자체도 정보성이 있어(`EXT_SOURCE_1` 결측 8.5% vs 관측 7.5%) 결측 플래그를 피처로 유지할 가치가 있다.

2. **상환부담률(annuity/income)은 완만하지만 단조적으로 곤란률과 연결된다** (구간별 7.2% → 8.8%). 그레이존 조건조정에서 "월 상환부담 축소" 축이 작동할 여지를 시사한다.

3. **소득대비신용액(credit/income)은 비단조**다(2~4배 구간 8.9%로 정점, 고배율 구간에서 오히려 하락). 단순히 대출금액만 줄이는 것이 항상 곤란률을 낮추지 않을 수 있다 — 프로젝트 **가설②**("조건 조정이 통하는/통하지 않는 고객 구분")를 뒷받침하는 관측 근거다.

4. **과거 거절비율은 강한 단조 신호**다. 과거 거절 0% 고객 7.1% vs 거절 75%↑ 고객 17.8%. `PREV_` 도메인이 모델에 유효한 정보를 더한다. 한편 이력 미보유(`HAS_PREV=0`) 고객의 곤란률(6.0%)이 보유 고객(8.2%)보다 낮은 점도 관측되었다(선택 편향 가능성, 통합 단계 검토 대상).

5. **train/test 분포는 대체로 유사**하나 `APP_CREDIT_INCOME_RATIO` 중앙값이 train 3.27 vs test 2.67로 차이가 있고, **과거신청 이력 보유율도 train 94.7% vs test 98.1%**로 달라 공변량 이동에 유의해야 한다. 나이·외부점수·상환부담률은 거의 동일하다.

6. **범주형(분석질문①):** 학력이 높을수록 곤란률이 단조 감소(Lower secondary 10.9% → Higher 5.4% → Academic 1.8%)하며, 성별(M 10.1% vs F 7.0%)과 주거형태(임대 12.3%·부모동거 11.7% vs 자가 7.8%)에서도 뚜렷한 차이가 관측된다.

## 4. 한계
- `TARGET`은 상환곤란이며 승인 거절이 아니다. 위 관계는 관측 상관이며 인과가 아니다.
- 승인 컷오프가 데이터에 없어 구제율·승인효과는 이 단계에서 주장하지 않는다.
- 구간화는 해석용이며 모델 입력은 연속형 원값을 사용한다.

## 5. 모델 단계 피처 후보 (담당 1 인계)
- **강신호:** `APP_EXT_SOURCE_MEAN`, `EXT_SOURCE_1/2/3` 원값 및 `_MISSING` 플래그
- **재무부담:** `APP_ANNUITY_INCOME_RATIO`(조건조정 핵심축), `APP_CREDIT_INCOME_RATIO`, `APP_CREDIT_GOODS_RATIO`
- **인적:** `APP_AGE_YEARS`, `APP_EMPLOYMENT_YEARS`, `APP_DAYS_EMPLOYED_ANOM`
- **과거이력:** `PREV_REFUSED_RATIO`, `PREV_APPROVED_RATIO`, `PREV_APPLICATION_COUNT`, `PREV_RECENT_DECISION_DAYS`, `HAS_PREV`

**인계 메모:** EXT_SOURCE의 강한 신호는 담당 2(외부 신용거래) 도메인과 개념적으로 연결되므로 통합 단계에서 상관·중복 점검이 필요하다.
