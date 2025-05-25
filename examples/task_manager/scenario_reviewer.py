# scenario_reviewer.py
class ScenarioReviewer:
    def __init__(self, sdd_system):
        self.sdd = sdd_system
    
    def review_scenarios(self):
        """Interactive review process"""
        print("=== ORIGINAL SCENARIOS ===")
        self.display_scenarios(self.sdd.scenarios)
        
        print("\n=== AI-GENERATED ADDITIONAL SCENARIOS ===")
        additional = self.sdd.generate_additional_scenarios()
        self.display_scenarios(additional)
        
        # Human approves/rejects/modifies scenarios
        approved_scenarios = self.interactive_review(additional)
        
        # Generate implementation from approved scenarios
        self.sdd.scenarios.extend(approved_scenarios)
        
        print("\n=== GENERATING IMPLEMENTATION ===")
        # This happens in background - human never sees code
        self.sdd.generate_implementation()
        
        print("\n=== VERIFICATION REPORT ===")
        verification = self.sdd.verify_implementation_matches_scenarios()
        self.display_verification(verification)
    
    def display_scenarios(self, scenarios):
        """Display scenarios in human-friendly format"""
        for scenario in scenarios:
            print(f"\n📋 {scenario['name']}")
            if 'given' in scenario:
                print(f"   Given: {scenario['given']}")
            print(f"   When: {scenario['when']}")
            print(f"   Then: {scenario['then']}")