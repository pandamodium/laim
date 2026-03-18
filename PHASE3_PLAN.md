# Phase 3: Business Formation & Endogenous Entry/Exit

**Status**: In Planning  
**Start Date**: March 18, 2026

## Overview

Phase 3 implements endogenous firm entry and exit mechanics. This adds "animal spirits" dynamics where entrepreneurs starting new firms can offset displacement from AI adoption. The system tracks firm dynamics with realistic entry/exit patterns.

---

## Key Mechanics

### 1. Firm Entry Process

**Entry Decision (Stochastic)**
```
Entrepreneur succeeds if:
  - Accumulated savings ≥ minimum_startup_capital
  - Random draw < entry_probability(t)
  
Where entry_probability(t) = 
  base_rate × 
  (1 + unemployment_premium if unemployed) ×
  (market_condition_factor) ×
  (1 - saturation_effect)
```

**Entry Sources**
- Unemployed workers considering entrepreneurship (existing mechanism)
- Employed workers with sufficient savings (new mechanism)
- Entry rate calibrated to ~3-5% annually (Kauffman benchmark)

**New Firm Initialization**
- Productivity: Draw from N(μ_incumbent, σ) where σ = 0.10 × μ_incumbent
- Initial workers: Random 1-5 humans + 0 AI (workers recruited in post-entry)
- Entry with existing capital stock (startup_capital parameter)
- Subject to same CES production as incumbents

### 2. Firm Exit Process

**Exit Decision**
- Any firm with losses in 2+ consecutive periods exits
- Upon exit, workers separate and return to unemployment
- Firm's AI capital (if any) becomes available to market

**Exit Handling**
- Remove from active firm list
- Track exit event in metrics
- Preserve firm history for analysis

### 3. Market Dynamics with Entry/Exit

**Market Re-equilibration**
- Fewer firms (after exits) → higher vacancies, wage pressure ↑
- More firms (after entries) → more competition, price pressure ↓
- Oligopoly becomes dynamic: N ≠ constant

**Entry Timing**
- Entrepreneurs act jointly after firm exit phase
- Prevent cascading entries/exits within single period by capping entry rate

---

## Implementation Tasks

### Task 1: Enhance Worker Entrepreneurship Logic
**File**: `src/agents/worker.py`

**Changes**:
- Current `consider_entrepreneurship()` only checks if agent should attempt entry
- Add return values indicating SUCCESS vs ATTEMPT
- Ensure proper state transition (employed → entrepreneur → firm owner or back to job search)

**Methods to modify**:
- `consider_entrepreneurship()` → returns (attempted: bool, succeeded: bool)

### Task 2: Create Entrepreneurship Entry System
**File**: `src/simulation/engine.py` (new method)

**New Method**: `_process_entrepreneurship_and_entry()`
```python
def _process_entrepreneurship_and_entry(self):
    """
    1. Identify potential entrepreneurs (unemployed with savings + employed with savings)
    2. Evaluate entry probability for each
    3. Process successful entries (create new firms)
    4. Remove successful entrepreneurs from labor force
    5. Track entry statistics
    """
```

**Process**:
1. Collect candidates from both unemployed and employed workers
2. For each candidate:
   - Compute entry probability (stochastic)
   - Draw random value
   - If success: remove from labor force, create firm, initialize with capital
3. Cap total entries to prevent cascading (~max 2% of unemployed becoming entrepreneurs)
4. Update metrics: `new_firms_entered`

### Task 3: Implement Dynamic Firm List Management
**File**: `src/simulation/engine.py`

**Changes**:
- Firms currently stored in list, assumed constant
- After Phase 3, needs dynamic update each period:
  1. Process firm exits (check loss history)
  2. Remove exited firms and separate their workers
  3. Process new entries (create Firm instances)
  4. Add new firms to active list
  5. Update firm_ids for consistency

**Impact**:
- `self.firms` list becomes dynamic
- Track cumulative entry/exit for analysis

### Task 4: Update Simulation Step Cycle
**File**: `src/simulation/engine.py` (update `step()` method)

**Current 12-step cycle**:
1. Compute market statistics
2. Update aggregate market wage (Phillips curve)
3. Update worker reservation wages
4. Execute firm exits (already present)
5. Execute worker steps
6. Clear and post jobs
7. Worker applications
8. Matching
9. Allocate matches
10. Production
11. Profits & R&D
12. Collect metrics

**Updated 13-step cycle** (add step 4.5):
1. Compute market statistics
2. Update aggregate market wage
3. Update worker reservation wages
4. **[NEW]** Process firm exits and remove exited workers
5. **[NEW]** Process entrepreneurship and new firm entry
6. Execute remaining worker steps (separations for non-entrepreneurs)
7. Clear and post jobs
8. Worker applications
9. Matching
10. Allocate matches
11. Production
12. Profits & R&D
13. Collect metrics

### Task 5: Add Heterogeneous Productivity to Firms
**File**: `src/agents/firm.py`

**Changes**:
- Firms need productivity attribute for differentiation
- Initialize new firms with productivity draw from distribution
- Store initial productivity for tracking
- Current system assumes all firms identical → enhance

**New attributes on FirmState**:
- `base_productivity`: Initial productivity at entry (used for diagnostics)
- `entry_period`: Period when firm entered (for age tracking)

### Task 6: Update Metrics & Tracking
**File**: `src/analytics/metrics.py`

**New Metrics** (to PeriodMetrics):
- `new_firms_entered`: Number of new firms entering this period
- `firms_exited`: Number of firms exiting this period
- `avg_firm_age`: Average age of active firms
- `num_entrepreneurs_active`: Number of persons currently attempting entrepreneurship
- `total_startup_capital_deployed`: Total capital allocated to new firms

**Updated Metrics**:
- `num_firms`: Now dynamic (not constant 3)
- `avg_firm_size`: Recalculated with dynamic firm count

### Task 7: Implement Startup Capital System
**File**: `src/config/parameters.py`

**New Parameters**:
- `minimum_startup_capital`: Savings threshold to become entrepreneur (default: 2 months wages)
- `entrepreneurship_capital_requirement`: How much starting capital new firm gets (default: 5 months wages)
- `entrepreneurship_success_rate_base`: Base annual rate (default: 0.05 = 5%)
- `entrepreneurship_market_saturation_factor`: How saturation affects entry (default: 0.5)

### Task 8: Testing
**File**: `tests/test_phase3_business_formation.py` (new)

**Test Coverage**:
1. Test entrepreneur entry probability calculation
2. Test new firm initialization (productivity, workers)
3. Test firm exit with loss history
4. Test dynamic firm list updates
5. Test market dynamics with changing firm count
6. Test entry/exit metrics tracking
7. Integration test: 50-period simulation with multiple entries/exits
8. Edge case: All firms exit (recovery possible?)

---

## Implementation Sequence

1. **Modify Worker Agent** (15 min)
   - Clarify return values from `consider_entrepreneurship()`
   
2. **Add Entry System to Engine** (30 min)
   - Implement `_process_entrepreneurship_and_entry()`
   
3. **Update Firm List Management** (20 min)
   - Replace firm exit check with full entry/exit coordination
   
4. **Enhance Firm Agent** (15 min)
   - Add productivity attributes and entry period tracking
   - Initialize new firms with property draw
   
5. **Update Simulation Step** (20 min)
   - Integrate entrepreneurship processing into 12-step cycle
   
6. **Update Configuration** (10 min)
   - Add new parameters with validation
   
7. **Update Metrics** (10 min)
   - Add new tracking fields
   
8. **Write Tests** (60 min)
   - 8 focused tests + 1 integration test
   
9. **Validation & Debugging** (30 min)
   - Run full 240-period simulations
   - Check dynamics are realistic

**Total Estimated Time**: ~3-4 hours execution

---

## Design Decisions

### Decision 1: Entry Probability Formula
- Simple multiplicative model vs. complex specification
- **Chosen**: Simple multiplicative (easier to interpret, calibrate)
- Formula: `base_rate × unemployed_premium × profitability_signal × (1 - saturation)`

### Decision 2: Startup Capital from Savings
- Could require borrowing/debt mechanics
- **Chosen**: Savings-based (simpler, matches micro evidence that entrepreneurs use personal capital)

### Decision 3: New Firm Initial Size
- Small (1-5 workers) vs. scaled-to-match-average
- **Chosen**: Small (1-5 workers) - reflects startup economics and growth over time

### Decision 4: Productivity Distribution
- Fixed at incumbent mean vs. drawn each entry
- **Chosen**: Drawn each entry - captures business idea heterogeneity

### Decision 5: Entry/Exit Coordination
- Simultaneous vs. sequential
- **Chosen**: Exits first (free up workers), then entries (can hire available workers) - realistic timing

---

## Success Criteria for Phase 3

✅ **Core Functionality**:
- Firms enter and exit dynamically
- Entry rate ≈ 3-5% annual on average
- Firm exit occurs on loss history as designed
- New firms initialize with random productivity

✅ **Market Dynamics**:
- Fewer incumbents after period of exits → wage pressure, unemployment rise
- Successful entries reduce unemployment
- Number of firms fluctuates realistically (not constant)

✅ **Metrics & Tracking**:
- Entry/exit metrics calculated correctly
- Firm age history maintained
- No missing or invalid data

✅ **Testing**:
- 9 tests all passing
- No edge case crashes
- Runs 240-period simulation successfully

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Entry cascades (too many firms) | Medium | High | Cap entry rate; use stochastic filtering |
| All firms exit (model collapse) | Low | Critical | Set entry rate such exits unlikely in SS; add safeguard |
| Productivity dispersion too large | Medium | Medium | Calibrate std dev at 10% of mean; monitor SS |
| Entry timing creates instability | Low | Medium | Exits before entries; smooth caps on entry |

---

## Next Phases (Preview)

- **Phase 4**: Enhanced R&D mechanics with firm-specific innovation
- **Phase 5**: Visualization and exploratory analysis
- **Phase 6+**: Calibration, heterogeneity, policy experiments

---

## References

- Kauffman Foundation entrepreneurship statistics
- Petrongolo & Pissarides (2001) on matching functions
- Hopenhayn (1992) on firm dynamics
