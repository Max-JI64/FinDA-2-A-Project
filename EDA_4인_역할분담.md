# 전체 Home Credit 데이터를 활용한 4인 병렬 EDA 계획

## 1. 목적과 범위

- EDA 역할만 4개 분석 영역으로 분할하며, EDA 종료 후 역할은 다시 정한다.
- 데이터 품질 확인, 전처리, 고객 단위 집계, 시각화, 결과 문서화는 네 명 모두 공통으로 수행한다.
- `data` 폴더의 8개 분석 테이블을 팀 전체가 빠짐없이 사용한다.
- `HomeCredit_columns_description.csv`는 변수 정의 검증에 사용한다.
- `sample_submission.csv`는 테스트 고객 ID와 향후 예측 결과 형식 검증에 사용한다.
- 각 담당자는 다른 담당자의 분석 결과를 기다리지 않고 자신의 원천 테이블에서 바로 `SK_ID_CURR` 단위 분석을 진행한다.

### 이번 EDA의 해석 경계

- `application_train.csv`의 `TARGET=1`은 현재 신청의 **승인 거절이 아니라 상환곤란(payment difficulty)**을 의미한다.
- `previous_application.csv`의 `NAME_CONTRACT_STATUS`는 과거 신청의 상태이며, 현재 신청의 승인 여부나 전체 거절 고객을 의미하지 않는다.
- 이번 EDA에서는 승인 가능성, 조건 변경 효과, 승인 구제율 또는 인과효과를 주장하지 않는다.
- 실제 금융사의 승인 기준과 컷오프는 데이터에 포함되어 있지 않으므로, 현재 단계는 상환곤란과 관련된 관측 패턴을 탐색하는 단계로 한정한다.

## 2. 전체 데이터 사용 기준

| 파일 | EDA 활용 목적 | 주 담당 |
|---|---|---|
| `application_train.csv` | 현재 신청자의 특성, 재무부담, 상환곤란 타깃 분석 | 담당 1, 타깃 연결은 전원 |
| `application_test.csv` | 학습·테스트 분포 및 고객 이력 커버리지 비교 | 담당 1, 커버리지 확인은 전원 |
| `previous_application.csv` | 과거 신청, 승인·거절 상태, 신청금액과 실제 신용액 분석 | 담당 1 |
| `bureau.csv` | 타 금융기관 신용거래, 활성부채, 연체 및 신용 규모 분석 | 담당 2 |
| `bureau_balance.csv` | 외부 신용거래의 월별 정상·연체·종료 상태 분석 | 담당 2 |
| `installments_payments.csv` | 예정 납부와 실제 납부의 지연·미납 행동 분석 | 담당 3 |
| `POS_CASH_balance.csv` | POS·현금대출의 잔여 할부와 월별 연체 분석 | 담당 4 |
| `credit_card_balance.csv` | 카드 한도 사용, 납부, 인출 및 월별 연체 분석 | 담당 4 |
| `HomeCredit_columns_description.csv` | 공식 변수 정의와 실제 CSV 헤더 대조 | 전원 |
| `sample_submission.csv` | `application_test` 고객 ID와 제출 형식 검증 | 전원 |

`HomeCredit_columns_description.csv`에 적힌 변수명과 실제 CSV 헤더가 다르면 실제 CSV 헤더를 코드의 기준으로 사용하고 차이를 기록한다.

## 3. 전원 공통 수행사항

각 담당자는 자신의 원천 테이블에 대해 다음 작업을 동일하게 수행한다.

1. 행·열 수, 기본키·외래키, 중복, 자료형을 확인한다.
2. 변수별 결측률과 특수값·비정상값을 확인한다.
3. 상대 날짜와 상대 월의 기준과 방향을 확인한다.
4. 학습·테스트 고객의 해당 이력 보유율을 비교한다.
5. 원시 거래·월별 이력을 `SK_ID_CURR`당 1행으로 집계한다.
6. `application_train.csv`에서 `SK_ID_CURR`, `TARGET`만 읽어 담당 도메인의 집계 결과와 결합한다.
7. `application_test.csv`의 `SK_ID_CURR`와 결합해 테스트 고객 커버리지와 분포 차이를 확인한다.
8. 담당 영역에서 최소 5개의 핵심 표·그래프와 3개 이상의 근거 기반 결론을 작성한다.
9. 모든 비율과 상환곤란률에 표본 수, 분모, 결측 처리 방식을 명시한다.
10. 분석 한계와 다음 모델 단계에 전달할 피처 후보를 정리한다.
11. 고객 단위 Parquet, 독립 실행 노트북, 리포트 섹션을 제출한다.

### 공통 전처리·시각화 규칙

- `SK_ID_CURR`, `SK_ID_PREV`, `SK_ID_BUREAU`는 연결용 식별자로만 사용하고 수치형 설명변수로 해석하지 않는다.
- 원본 행과 값은 삭제하거나 덮어쓰지 않는다.
- 이상치가 큰 금액 변수는 원본 요약통계를 유지하면서 그래프에만 로그축 또는 1·99백분위 표시 범위를 적용한다.
- 0 이하인 분모로 비율을 계산하지 않으며, 결과를 `NaN`으로 두고 별도의 오류 플래그를 만든다.
- 범주별 비교에서는 표본 수를 함께 표시한다.
- 표본이 500건 미만이거나 전체의 1% 미만인 범주는 시각화에서 `OTHER`로 묶되 원본 범주는 보존한다.
- 상환곤란률 비교에는 가능한 경우 95% Wilson 신뢰구간을 함께 표시한다.
- 월별 테이블은 최근 3·6·12개월, 일 단위 테이블은 최근 90·180·365일을 공통 기간창으로 사용한다.
- 대용량 파일은 100만 행 단위 청크로 읽으며, 최종 통계는 샘플이 아닌 전체 행을 기준으로 계산한다.
- 모든 코드에서 저장소 루트 기준 상대경로를 사용한다.

## 4. 4인 독립 EDA 역할 분담

### 담당 1 — 현재 신청 및 과거 신청 분석

**원천 데이터**

- `application_train.csv`
- `application_test.csv`
- `previous_application.csv`

**분석 질문**

1. 현재 신청자의 인구통계·소득·고용·주거·신청 조건은 어떻게 분포하는가?
2. 소득 대비 대출액과 상환액이 높아질수록 관측 상환곤란률은 어떻게 달라지는가?
3. 외부 신용점수와 결측 여부에 따라 상환곤란률은 어떻게 달라지는가?
4. 과거 신청 횟수, 승인·거절 비율, 최근 신청 시점은 현재 상환곤란과 어떤 관계가 있는가?
5. 학습 데이터와 테스트 데이터의 주요 신청자 특성에 차이가 있는가?

**주요 파생지표**

- `APP_CREDIT_INCOME_RATIO`: `AMT_CREDIT / AMT_INCOME_TOTAL`
- `APP_ANNUITY_INCOME_RATIO`: `AMT_ANNUITY / AMT_INCOME_TOTAL`
- `APP_CREDIT_GOODS_RATIO`: `AMT_CREDIT / AMT_GOODS_PRICE`
- `APP_AGE_YEARS`: `-DAYS_BIRTH / 365.25`
- `APP_EMPLOYMENT_YEARS`: 특수값을 제거한 근속기간
- `PREV_APPLICATION_COUNT`: 과거 신청 수
- `PREV_APPROVED_RATIO`, `PREV_REFUSED_RATIO`: 과거 신청 상태 비율
- `PREV_RECENT_DECISION_DAYS`: 가장 최근 과거 신청 이후 기간
- `PREV_CREDIT_APPLICATION_RATIO`: 과거 신청액 대비 실제 신용액

`DAYS_EMPLOYED=365243`은 실제 근속기간이 아니므로 `NaN`으로 치환하고 특수값 플래그를 별도로 생성한다.

### 담당 2 — 외부 신용거래 및 월별 연체 분석

**원천 데이터**

- `bureau.csv`
- `bureau_balance.csv`

**분석 질문**

1. 타 금융기관 거래 수와 활성 신용거래 비율은 어떻게 분포하는가?
2. 외부 총부채와 신용공여액 대비 부채 비율은 상환곤란과 어떤 관계가 있는가?
3. 현재 연체일, 연체금액, 과거 최악 연체 상태는 상환곤란률과 어떤 관계가 있는가?
4. 최근 3·6·12개월의 연체 빈도와 연체 심도는 어떻게 변화하는가?
5. 외부 신용이력이 없는 고객과 있는 고객의 상환곤란률에 차이가 있는가?

**주요 파생지표**

- `BUR_CREDIT_COUNT`: 외부 신용거래 수
- `BUR_ACTIVE_RATIO`: 활성 거래 비율
- `BUR_TOTAL_CREDIT`, `BUR_TOTAL_DEBT`: 총 신용공여액과 총부채
- `BUR_DEBT_CREDIT_RATIO`: 총부채/총 신용공여액
- `BUR_MAX_DAYS_OVERDUE`: 최대 현재 연체일
- `BUR_TOTAL_OVERDUE`: 총 연체금액
- `BUR_RECENT_CREDIT_DAYS`: 가장 최근 외부 신용거래 이후 기간
- `BB_MAX_STATUS`: 관측된 최악 월별 연체 상태
- `BB_DELINQUENT_MONTH_RATIO`: 연체 월 비율
- `BB_DELINQUENT_COUNT_3M`, `BB_DELINQUENT_COUNT_6M`, `BB_DELINQUENT_COUNT_12M`

`bureau_balance.csv`는 먼저 `SK_ID_BUREAU` 단위로 집계한 다음 `bureau.csv`와 연결하고, 마지막에 `SK_ID_CURR` 단위로 집계한다. 원시 월별 행을 Application 테이블과 직접 조인하지 않는다.

월별 상태는 다음과 같이 구분한다.

- `0`: 정상
- `1`~`5`: 연체 심도
- `C`: 종료
- `X`: 상태 미상

### 담당 3 — 할부 상환 행동 분석

**원천 데이터**

- `installments_payments.csv`

**분석 질문**

1. 예정 납부일과 실제 납부일의 차이는 어떻게 분포하는가?
2. 지연 납부와 미납금액이 큰 고객의 상환곤란률은 어떻게 다른가?
3. 최근 90·180·365일 상환 행동에서 위험 신호가 강화되는가?
4. 반복 지연 고객과 일시 지연 고객은 어떤 차이가 있는가?
5. 상환계획 변경 또는 분할 지급이 많은 고객의 특징은 무엇인가?

**주요 파생지표**

- `INS_PAYMENT_DELAY_DAYS`: `DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT`
- `INS_PAYMENT_SHORTFALL`: `AMT_INSTALMENT - AMT_PAYMENT`
- `INS_LATE_PAYMENT_RATIO`: 지연 납부 회차 비율
- `INS_UNDERPAYMENT_RATIO`: 예정액 미만 납부 회차 비율
- `INS_EARLY_PAYMENT_RATIO`: 조기납부 회차 비율
- `INS_MAX_DELAY_DAYS`, `INS_MEAN_DELAY_DAYS`
- `INS_TOTAL_SHORTFALL`
- `INS_LATE_COUNT_90D`, `INS_LATE_COUNT_180D`, `INS_LATE_COUNT_365D`
- `INS_VERSION_COUNT`: 상환계획 버전 수

같은 `SK_ID_PREV`와 할부 회차에 여러 지급 행이 존재할 수 있으므로, 예정액과 실제 납부액을 회차 단위로 먼저 정리한 뒤 고객 단위로 집계한다.

### 담당 4 — POS·현금대출 및 신용카드 행동 분석

**원천 데이터**

- `POS_CASH_balance.csv`
- `credit_card_balance.csv`

**분석 질문**

1. POS·현금대출의 월별 연체와 잔여 할부는 어떻게 분포하는가?
2. 최근 연체가 증가하는 고객과 안정적인 고객은 어떤 차이가 있는가?
3. 신용카드 한도 사용률과 납부 행동은 상환곤란과 어떤 관계가 있는가?
4. 현금인출 비중이 높은 고객은 잔액·연체 측면에서 어떤 특징을 보이는가?
5. 카드 또는 POS 이력이 없는 고객과 있는 고객의 상환곤란률은 어떻게 다른가?

**주요 파생지표**

- `POS_MAX_DPD`, `POS_MAX_DPD_DEF`
- `POS_DELINQUENT_MONTH_RATIO`
- `POS_REMAINING_INSTALLMENTS`
- `POS_DELINQUENT_COUNT_3M`, `POS_DELINQUENT_COUNT_6M`, `POS_DELINQUENT_COUNT_12M`
- `CC_UTILIZATION_RATIO`: `AMT_BALANCE / AMT_CREDIT_LIMIT_ACTUAL`
- `CC_PAYMENT_MIN_RATIO`: `AMT_PAYMENT_CURRENT / AMT_INST_MIN_REGULARITY`
- `CC_CASH_DRAWING_RATIO`: ATM 현금인출액/전체 인출·사용액
- `CC_MAX_DPD`, `CC_DELINQUENT_MONTH_RATIO`
- `CC_BALANCE_TREND`, `CC_UTILIZATION_TREND`

월별 테이블은 각 `SK_ID_PREV`의 월별 추이를 먼저 정리한 뒤 `SK_ID_CURR` 단위로 집계한다.

## 5. 공통 데이터 인터페이스

병렬 작업 전에 팀 전체가 피처 접두사와 출력 형식을 확정한다.

| 접두사 | 의미 |
|---|---|
| `APP_` | 현재 신청 |
| `PREV_` | 과거 신청 |
| `BUR_` | 외부 신용거래 |
| `BB_` | 외부 신용거래 월별 상태 |
| `INS_` | 할부 상환 |
| `POS_` | POS·현금대출 |
| `CC_` | 신용카드 |

각 담당자의 고객 단위 산출물은 다음 공통 구조를 따른다.

1. `SK_ID_CURR`
2. `HAS_<DOMAIN>`: 해당 도메인의 이력 존재 여부
3. 담당 도메인 접두사가 붙은 고객 단위 피처

이력이 없는 고객은 다음 기준으로 처리한다.

- 거래·관측 건수: 0
- 금액, 비율, 최근값, 추세: `NaN`
- 이력 유무: `HAS_<DOMAIN>=0`

각 담당자는 서로 다른 노트북·스크립트·출력 파일만 수정한다. 분석 중 하나의 공통 노트북을 동시에 편집하지 않는다.

권장 구조는 다음과 같다.

```text
notebooks/eda/
├─ 01_application_previous_eda.ipynb
├─ 02_bureau_eda.ipynb
├─ 03_installments_eda.ipynb
└─ 04_pos_credit_card_eda.ipynb

src/eda/
├─ application_previous_features.py
├─ bureau_features.py
├─ installments_features.py
└─ pos_credit_card_features.py

reports/eda/
├─ sections/
├─ figures/
├─ tables/
└─ EDA_통합리포트.md
```

원본과 중간 Parquet은 `data/` 아래에 두고 Git에 커밋하지 않는다.

네 도메인 결과가 완성되면 `SK_ID_CURR`를 기준으로 수평 결합한다. 결합 데이터는 Application 고객당 1행을 유지해야 하며, 결합 전에 각 도메인 결과에서 `SK_ID_CURR`의 유일성을 검증한다.

## 6. 1주 진행 일정

| 일정 | 작업 |
|---|---|
| 1일차 오전 | 전원이 공통 템플릿, 피처 접두사, 기간창, 그래프 규칙, 파일 구조 확정 |
| 1일차 오후~3일차 | 네 담당 영역을 동시에 독립 분석하고 고객 단위 집계 생성 |
| 4일차 오전 | 담당 1↔3, 담당 2↔4 교차 코드·결과 리뷰 |
| 4일차 오후 | 리뷰 결과 반영, 결론과 데이터 한계 수정 |
| 5일차 오전 | 네 고객 단위 결과를 `SK_ID_CURR` 기준으로 통합 |
| 5일차 오후 | 통합 EDA 리포트, 모델 단계 피처 후보, 발표용 핵심 결론 정리 |

README에는 EDA 진행상태, 4인 역할표, 통합 리포트 링크만 추가하고 상세 분석 내용은 별도 통합 리포트에 유지한다.

## 7. 검증 및 완료 기준

### 데이터 검증

- `data/README.md`에 기록된 각 CSV의 행·열 수와 실제 처리 결과를 대조한다.
- 청크 처리한 원시행 수의 합이 파일 전체 행 수와 일치해야 한다.
- `HomeCredit_columns_description.csv`와 실제 헤더의 차이를 확인하고 기록한다.
- `sample_submission.csv`의 48,744개 `SK_ID_CURR`가 `application_test.csv`와 정확히 일치해야 한다.
- `application_train.csv`의 `SK_ID_CURR`는 유일해야 한다.
- `TARGET=1`은 24,825건인지 확인한다.

### 집계·결합 검증

- 각 도메인 고객 단위 결과에서 `SK_ID_CURR`는 유일해야 한다.
- 비율 파생변수에 양·음의 무한대가 없어야 한다.
- 거래·월별 집계에 사용된 관측행 수 합계가 원본 행 수와 일치해야 한다.
- 도메인 결과를 Application과 결합한 뒤 Application 행 수가 증가하거나 감소하지 않아야 한다.
- 이력이 없는 고객과 결측값이 구분되어야 한다.

### 산출물 검증

- 네 개의 담당 노트북이 커널 재시작 후 처음부터 끝까지 독립 실행되어야 한다.
- 각 담당 영역에 최소 5개 표·그래프와 3개 근거 기반 결론이 있어야 한다.
- 모든 주요 그래프에 제목, 축 단위, 표본 수 또는 분모가 표시되어야 한다.
- 통합 리포트에 네 영역의 결론, 공통 위험 신호, 서로 상충하는 결과, 모델 단계 피처 후보, 데이터 한계가 포함되어야 한다.
- 전체 데이터 사용 체크리스트에서 분석 CSV 8개, 변수 설명 파일, 제출 형식 파일이 모두 확인되어야 한다.

## 8. 가정과 제외 범위

- 팀원 네 명의 Python·통계 숙련도는 비슷한 수준으로 가정한다.
- 이번 역할 분담은 EDA 단계에만 적용한다.
- 결과 문서는 한국어로 작성하고 실제 변수명과 코드명은 영어 원문을 유지한다.
- 모델 학습, SHAP, 승인 컷오프 설정, 금액 조정 시뮬레이션, Claude API, Streamlit은 이번 EDA 범위에서 제외한다.
- `TARGET`만으로 실제 금융사의 승인 정책을 재현할 수 없음을 모든 결과물에 명시한다.
- EDA에서 확인된 관계는 관측 상관관계이며, 변수 변경이 상환곤란률을 낮춘다는 인과관계로 해석하지 않는다.
