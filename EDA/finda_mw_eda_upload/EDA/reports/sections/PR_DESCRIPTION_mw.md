# PR: 담당1 application·previous EDA 및 고객단위 피처

## 1. 작업 목적
담당 1(현재 신청 + 과거 신청) 도메인의 EDA를 수행하고, `SK_ID_CURR` 단위 피처(`APP_`/`PREV_`)를 생성한다. 재무부담·외부점수·과거 신청 이력과 상환곤란(TARGET)의 관측 관계를 정리하고 모델 단계 피처 후보를 도출한다.

## 2. 주요 변경 파일
- `EDA/notebooks/01_application_previous_eda_mw.ipynb` — 독립 실행 EDA 노트북
- `EDA/src/application_previous_features_mw.py` — 재사용 피처 모듈
- `EDA/figures/fig01~08_*_mw.png` — 핵심 그래프 8종
- `EDA/reports/sections/01_application_previous_mw.md` — 리포트 섹션
- (파생 `app_prev_features_mw.parquet` 은 .gitignore 대상으로 커밋 제외)

## 3. 실행 방법
저장소 루트에서 노트북을 커널 재시작 후 처음부터 실행하면 원본(`data/`)으로부터 그래프와 파생 parquet이 재생성된다. 경로는 전부 저장소 루트 기준 상대경로이며 seed는 42로 고정.

## 4. 생성된 결과
- 고객 단위 산출물 307,511행 × 17열 (SK_ID_CURR 유일, Application 행수 보존)
- 표 11종 + 그래프 8종 + 근거 결론 6개

## 5. 검증 내용
- README 실측값과 일치: train 307,511행, TARGET=1 24,825건(8.07%), train/test ID 중복 0
- 상대 날짜 방향(음수=과거) 검증, 0 분모 안전 나눗셈(inf 없음) 확인
- 결합 후 Application 행수 불변, SK_ID_CURR 유일성 확인
- 노트북 커널 재시작 후 전 셀 오류 0으로 실행

## 6. 확인이 필요한 사항
- test 과거신청 이력 보유율(98.1%)이 train(94.7%)보다 높음 → 통합/모델 단계에서 공변량 이동 검토
- EXT_SOURCE 신호가 담당 2(외부 신용거래) 도메인과 개념적으로 연결됨 → 통합 시 상관·중복 점검

## 해석 경계 (규칙 7)
`TARGET`은 상환곤란이며 승인 거절이 아니다. 관측 상관이며 인과가 아니고, 승인 컷오프·구제율은 이 단계에서 주장하지 않는다.
