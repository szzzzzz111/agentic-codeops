## MODIFIED Requirements

### Requirement: Live evaluator 区分 provider conformance 与 execution integrity

Live evaluator MUST distinguish provider/system conformance failures from evaluation integrity failures. It MUST NOT
generate tracked provider conformance evidence when the evaluated provider was not fairly contacted.

#### Scenario: Transport blocker 不生成 tracked conformance evidence

- **WHEN** a live run attempts provider-backed cases
- **AND** every provider-backed attempt has `availability=unavailable`
- **AND** no provider-backed attempt has a complete real response with finish reason、returned model and usage
- **THEN** the run MUST be classified as transport/integrity blocked
- **AND** the runner MUST NOT generate PASS attestation
- **AND** the runner MUST NOT generate evaluated-failure record
- **AND** the local report MAY record redacted diagnostic codes
- **AND** documentation MUST NOT describe the result as provider conformance FAIL

#### Scenario: Redacted transport diagnostics are allowlisted

- **WHEN** a provider call fails before a usable model response is available
- **THEN** the local report MAY include allowlisted diagnostic fields such as `phase`、`error_class` and `status_class`
- **AND** the report MUST NOT include API key、complete URL、headers、payload、prompt、EvidencePack、raw answer、
  raw exception message、traceback、HTTP body、diff、reasoning content or raw fingerprint

#### Scenario: Confirmed provider contact can still produce conformance FAIL evidence

- **WHEN** at least one provider-backed attempt completes with a usable model response
- **AND** the run completes with conformance hard gate failures rather than integrity failures
- **THEN** the runner MAY generate an evaluated-failure record under the existing allowlist schema
- **AND** that record MUST remain distinct from transport/integrity blocker outcomes

#### Scenario: Unconfirmed live shell fails closed before provider calls

- **WHEN** live evaluation is launched without explicit network-capable execution confirmation
- **THEN** the runner MUST stop before provider calls
- **AND** the result MUST NOT consume live call budget
- **AND** the result MUST NOT generate PASS attestation or evaluated-failure record
- **AND** default deterministic verification MUST remain network-free
