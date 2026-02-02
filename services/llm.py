"""
LLM Service for ChurnGuard AI Chatbot
Handles AI response generation using Groq API
"""

import os
from typing import Dict, Any, Optional

# Try to import Groq
try:
    from groq import Groq
    USE_GROQ = True
except ImportError:
    USE_GROQ = False
    print("⚠ Groq not installed. Install with: pip install groq")


class LLMService:
    """Service for generating AI responses"""

    def __init__(self):
        """Initialize LLM service with Groq API"""

        # Initialize Groq client
        if USE_GROQ and os.getenv("GROQ_API_KEY"):
            try:
                self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                self.provider = "groq"
                print("✓ Groq API initialized successfully")
            except Exception as e:
                print(f"❌ Groq initialization error: {str(e)}")
                self.provider = None
        else:
            self.provider = None
            print("⚠ No GROQ_API_KEY found. Using intelligent fallback responses.")
            print("  Add GROQ_API_KEY to your .env file to enable AI")

    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate AI response using configured LLM provider

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response

        Returns:
            AI-generated response string
        """
        try:
            if self.provider == "groq":
                return self._groq_response(prompt, max_tokens)
            else:
                return self._fallback_response(prompt)
        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return "I'm having trouble connecting right now. Please try again!"

    def _groq_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Groq API"""
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert customer retention analyst specializing in telecom churn analysis. Provide concise, data-driven insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",  # Groq's best model
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API error: {str(e)}")
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Intelligent fallback responses based on your telecom data"""
        prompt_lower = prompt.lower()

        # Churn analysis
        if "churn" in prompt_lower and "why" in prompt_lower:
            return """Based on your 1.2M customer telecom analysis, churn is happening due to:

**Top 3 Drivers:**
1. **Service Quality Issues (32%)** - Network connectivity problems and service disruptions are the #1 cause
2. **Competitive Pricing (28%)** - Competitors offering better deals and promotions
3. **Poor Customer Service (24%)** - Long wait times and unresolved support tickets

**High-Risk Customer Segments:**
- Month-to-month contract customers: 42% churn rate
- Customers in first 6-9 months: Early lifecycle churn risk
- 3+ support tickets: 55% churn probability
- High network downtime areas: Significantly elevated risk

**Key Insight:** With your 18.5% churn rate affecting 222K customers and putting $289.31M revenue at risk, focusing on service quality improvements (the 32% driver) would yield the highest ROI compared to discounting strategies."""

        # Revenue generation
        elif "revenue" in prompt_lower:
            return """Your $1.49B telecom revenue breakdown:

**Primary Revenue Channels:**
1. **Online Channel**: $4.23B (44.9% of total)
2. **Store Channel**: $3.30B (35.1% of total)
3. **Agent Channel**: $1.88B (20.0% of total)

**Key Metrics:**
- Total Monthly Revenue: $1.49 billion
- Revenue at Risk: $289.31M (19.4% of total revenue)
- Average Revenue Per User (ARPU): $1,241.70
- Revenue Protected: $1.20B

**Revenue Optimization Opportunity:**
Your high ARPU of $1,241.70 indicates a valuable customer base. Even a 3% churn reduction would protect $40-50M annually. Focus retention efforts on high-ARPU customers (2-year contract customers averaging $95/month) rather than broad discounting across all segments."""

        # Segment and risk analysis
        elif "segment" in prompt_lower or "risk" in prompt_lower:
            return """Customer segments at highest risk (from your 1.2M customer base):

**Critical Risk Segments:**

1. **Retail Segment** (HIGHEST EXPOSURE)
   - Customers: 1,052,448 (87.7% of customer base)
   - Churn Rate: 19%
   - Revenue at Risk: $254.3M
   - **Priority Action:** #1 focus for retention programs

2. **SME Segment**
   - Customers: 147,552 (12.3% of customer base)
   - Churn Rate: 18%
   - Revenue at Risk: $34.9M
   
3. **South Region** (Geographic Priority)
   - Highest Revenue: $516.22M
   - Highest Risk: $102M at risk
   - Churn Rate: 24.63%

4. **Month-to-Month Contracts** (Contract Type Risk)
   - Churn Rate: 42% (vs 12% for 2-year contracts)
   - High conversion potential: 30% success rate

**Recommended Focus:**
Target month-to-month Retail customers in the South region with 6-12 month contract conversion incentives. This segment represents the highest revenue risk concentration and has proven conversion rates of 30%."""

        # Retention strategies
        elif "retention" in prompt_lower or "strateg" in prompt_lower:
            return """Top retention strategies for your telecom operation (Goal: 18.5% → 15% churn):

**High-Impact Tactics (Proven ROI):**

1. **Early Lifecycle Programs** (Highest Impact)
   - **Issue:** Most churn occurs in first 6-9 months
   - **Action:** Enhanced onboarding with 30-60-90 day check-ins
   - **Expected Impact:** 15-20% reduction in new customer churn

2. **Service Quality First** (Addresses 32% of Churn)
   - **Issue:** Network issues cause 32% of all churn
   - **Action:** Reduce downtime in high-churn regions, priority infrastructure investment
   - **ROI:** Better than discounts - addresses root cause
   - **Focus Area:** South region network upgrades

3. **Proactive Support Intervention** (18% Improvement)
   - **Issue:** Customers with 3+ support tickets have 55% churn rate
   - **Action:** Auto-escalate after 2 tickets, resolve within 24 hours
   - **Expected Impact:** 18% churn improvement in high-ticket segment

4. **Contract Conversion Program** (23% Reduction)
   - **Target:** Month-to-month customers (42% churn rate)
   - **Offer:** 10-15% discount for 6-month commitment
   - **Expected Impact:** 23% churn reduction, 30% conversion rate
   - **ROI:** 6.4x return on retention investment

**Combined Revenue Protection:**
Implementing these 4 strategies could reduce churn from 18.5% to 15%, protecting $40-50M annually from your $289.31M revenue at risk."""

        # Regional analysis
        elif "region" in prompt_lower or "south" in prompt_lower:
            return """Regional churn analysis across your 4 telecom regions:

**Priority Ranking by Revenue Risk:**

1. **South Region** (HIGHEST PRIORITY)
   - Total Revenue: $516.22M (highest of all regions)
   - Revenue at Risk: $102M (highest absolute exposure)
   - Churn Rate: 24.63%
   - Customer Count: ~300,000
   - **Action:** Deploy dedicated retention team + network infrastructure upgrades

2. **West Region**
   - Total Revenue: $375.03M
   - Revenue at Risk: $73M
   - Churn Rate: 25.18% (highest churn rate)
   - **Action:** Investigate competitive pricing pressures

3. **North Region**
   - Total Revenue: $372.16M
   - Revenue at Risk: $72M
   - Churn Rate: 24.78%
   - **Action:** Standard retention programs

4. **East Region**
   - Total Revenue: $226.63M
   - Revenue at Risk: $43M (lowest risk)
   - Churn Rate: 25.40%

**Key Strategic Insight:**
While churn rates are relatively balanced (24.6-25.4% across regions), the South region's combination of highest revenue generation AND highest absolute risk exposure ($102M) makes it the clear #1 priority for retention investment. A 3-5% churn reduction in South alone could protect $30-40M annually."""

        # Customer insights
        elif "customer" in prompt_lower:
            return """Comprehensive customer base insights from your 1.2M customers:

**Demographics & Overview:**
- Total Active Customers: 1,200,000
- Churned Customers: 222,000 (18.5%)
- Retained Customers: 978,000 (81.5%)
- Average Customer Tenure: 32 months
- Average Revenue Per User (ARPU): $1,241.70

**Customer Segment Breakdown:**
1. **Premium Customers** (2-year contracts)
   - Churn Rate: 12% (lowest)
   - Average Revenue: $95/month
   - Loyalty Level: Highest
   - Characteristics: Long tenure, low support tickets
   
2. **Standard Customers** (1-year contracts)
   - Churn Rate: 24% (moderate)
   - Average Revenue: $65/month
   - Conversion Opportunity: Target for 2-year upgrades
   
3. **At-Risk Customers** (Month-to-month)
   - Churn Rate: 42% (highest)
   - Average Revenue: $45/month
   - **Action Required:** Top priority for retention

**Regional Distribution:**
- South: ~300,000 customers (25.4% churn)
- West: ~300,000 customers (25.2% churn)
- North: ~300,000 customers (24.8% churn)
- East: ~300,000 customers (25.4% churn)

**Critical Business Finding:**
Converting just 30% of month-to-month customers to annual contracts could protect $40-50M in annual revenue while improving customer lifetime value by an average of 8-12 months."""

        # Default comprehensive response
        else:
            return """I'm your AI Retention Analyst for the ChurnGuard telecom platform. I can analyze your 1.2M customer dataset and provide insights on:

**Current Business Status:**
- 1.2M total customers with 18.5% churn rate
- $289.31M revenue at risk
- $1,241.70 ARPU (high-value customer base)

**I Can Answer Questions About:**

📊 **Churn Analysis**
- Why customers are leaving (32% service quality, 28% pricing, 24% support)
- Which segments have highest churn rates
- Early warning signals and risk indicators

💰 **Revenue Intelligence**
- How $1.49B revenue is generated (Online 45%, Store 35%, Agent 20%)
- Revenue optimization opportunities
- ARPU trends and high-value customer retention

🎯 **Customer Segments**
- Retail (1.05M, 19% churn) vs SME (147K, 18% churn)
- Regional performance: South ($102M at risk), West, North, East
- Contract types: Month-to-month (42% churn) vs Annual (24%) vs 2-year (12%)

📈 **Retention Strategies**
- Proven tactics to reduce churn from 18.5% to 15%
- ROI analysis of different retention programs
- Early lifecycle, service quality, and proactive support strategies

**Try asking specific questions like:**
- "Why is our churn rate 18.5%?"
- "Which customer segment has the highest revenue at risk?"
- "How can we reduce churn in the South region?"
- "What's the ROI of improving service quality vs offering discounts?"

What would you like to know about your customer retention?"""


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_llm_response(prompt: str) -> str:
    """
    Convenience function to get LLM response

    Args:
        prompt: The question/prompt to send to the LLM

    Returns:
        AI-generated response
    """
    service = get_llm_service()
    return service.generate_response(prompt)