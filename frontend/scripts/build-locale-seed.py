#!/usr/bin/env python3
"""Seed en/he locale JSON — extended manually in repo; run to regenerate base."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "locales"

EN = {
  "app": {
    "language": "Language",
    "languageEn": "EN",
    "languageHe": "עב",
    "brand": {"title": "Insurance Customer 360", "tagline": "Cloudera AI · Business & customer views"},
    "a11y": {"applicationAreas": "Application areas", "administrationNav": "Administration"},
    "dataFreshness": {
      "label": "Data freshness",
      "warehouse": "Warehouse",
      "metricsCache": "Metrics cache",
      "portfolioCache": "Portfolio cache",
      "churnScores": "Churn scores",
      "churnScored": "{{date}} ({{count}} customers)"
    }
  },
  "nav": {
    "workspace": "Workspace",
    "business": {"title": "The business", "desc": "Book, cohorts, and portfolio KPIs"},
    "customer": {"title": "The customer", "desc": "360 profile, insights, and outreach"},
    "engagement": {"title": "Engagement", "desc": "Touchpoints, influence, and next best action", "short": "Engagement"},
    "products": {"title": "Products", "desc": "Product heatmap and customer drill-down"},
    "admin": {"section": "Administration", "title": "Data & admin", "desc": "Health, warehouse, data source"}
  },
  "common": {
    "loading": "Loading…",
    "yes": "Yes",
    "no": "No",
    "none": "None",
    "showAll": "Show all",
    "emDash": "—",
    "a11y": {"breadcrumb": "Breadcrumb"}
  },
  "errors": {
    "overviewLoadFailed": "Failed to load overview",
    "productsLoadFailed": "Failed to load products",
    "engagementLoadFailed": "Failed to load engagement hub",
    "adminLoadFailed": "Failed to load admin data",
    "customersLoadFailed": "Failed to load customers",
    "invalidCustomerId": "Invalid customer ID",
    "customerNotFound": "Customer not found",
    "copilotUnreachable": "Could not reach the copilot. Check that the API is running.",
    "boundary": {
      "title": "Something went wrong",
      "hint": "Try a hard refresh. If this persists, restart the application and confirm frontend/dist matches the running API version.",
      "reload": "Reload page"
    }
  },
  "cohort": {
    "fullBook": "Full book",
    "filteredCohort": "Filtered cohort",
    "filteredBy": "Filtered by “{{label}}”",
    "fullActiveBook": "Full active customer book",
    "segments": {
      "customers_all": "All customers",
      "with_policies": "With policies",
      "with_foreclosures": "With foreclosures",
      "with_investments": "With investments",
      "with_insurance_status": "With insurance status",
      "with_market_products": "With market products"
    }
  },
  "business": {
    "domainFilter": {
      "helperAnalytics": "Click a card to filter analytics. Click again to clear.",
      "helperCustomerList": "Click a card to filter the customer list. Click again to clear.",
      "refreshedAt": "Counts refreshed {{time}}",
      "policyFoot": "{{active}} active · avg {{avg}} / customer",
      "allBookFoot": "{{policies}} policies · {{active}} active"
    },
    "compare": {
      "label": "Compare to",
      "none": "No comparison",
      "loading": "Loading comparison cohort…",
      "panelTitle": "Cohort comparison",
      "panelLede": "Side-by-side KPIs for the selected card vs a second cohort (charts above stay on the primary selection).",
      "metric": "Metric",
      "delta": "Delta",
      "deltaVsCompare": "{{sign}}{{pct}}% vs compare",
      "deltaPts": "{{pts}} pts"
    },
    "cohort": {
      "filteredBadge": "Filtered cohort",
      "vsBookLead": "This slice is {{share}} of total customer value in the full book (reference below).",
      "shareOfBook": "{{pct}}% of book"
    },
    "portfolio": {
      "sectionGrowth": "Book growth & churn outlook",
      "ledeFiltered": "{{caption}} — KPIs and charts reload when you change the overview cards above.",
      "ledeFull": "Portfolio KPIs with industry-aligned churn forecast on total customer value.",
      "bookHistory": "Book history: {{range}}.",
      "mobileLead": "{{caption}} · benchmark status on each card",
      "objectivesTitle": "Strategic objective trends",
      "objectivesDefaultNote": "Trends mapped to long-term savings growth, insurance premium momentum, and customer engagement.",
      "updating": "Updating analytics…",
      "retentionRunScoring": "Run churn scoring to estimate portfolio lapse rate.",
      "retentionSub": "Book-weighted 12m lapse {{pct}}% · HIGH {{high}} · MED {{med}} · LOW {{low}}",
      "valueAtRiskSub": "Σ customer value × lapse probability (tier-weighted when ML score missing)",
      "policyRecordsSub": "{{active}} active · avg {{avg}} / customer",
      "highRiskShareSub": "{{count}} high-risk customers",
      "retentionQueueHint": "Open retention queue in copilot →",
      "kpi": {
        "totalBookValue": "Total book value",
        "retentionForecast": "12m retention (forecast)",
        "valueAtChurnRisk": "Value at churn risk",
        "activeCustomers": "Active customers",
        "policyRecords": "Policy records",
        "avgCustomerValue": "Avg customer value",
        "highRiskBookShare": "High-risk book share",
        "bookGrowthHistory": "Book growth (history)"
      }
    },
    "kpi": {
      "objective": "Objective: {{target}}",
      "thermo": {
        "atOrBelow": "At or below objective",
        "ofLimit": "{{pct}}% of limit",
        "ofObjective": "{{pct}}% of objective",
        "a11y": "{{status}} — {{detail}}"
      }
    },
    "compareRows": {
      "activeCustomers": "Active customers",
      "totalBookValue": "Total book value",
      "valueAtChurnRisk": "Value at churn risk",
      "retentionForecast": "12m retention (forecast)"
    },
    "vsBookStats": {
      "customers": "Customers",
      "totalBookValue": "Total book value",
      "policyRecords": "Policy records",
      "avgCustomerValue": "Avg customer value"
    },
    "historyMonths": "{{first}} – {{last}} ({{count}} months)"
  },
  "mobile": {
    "backToCopilot": "← Copilot",
    "focusTitle": {
      "business": "Business KPIs",
      "customers": "Customers",
      "customerProfile": "Customer profile",
      "products": "Products",
      "engagement": "Engagement",
      "admin": "Admin",
      "details": "Details"
    }
  },
  "copilot": {
    "title": "Executive copilot",
    "shortTitle": "Copilot",
    "lede": {
      "phone": "Ask about the book, then open a link to focus that page on your phone.",
      "desktop": "Ask about the book; links change the main view or open the retention queue."
    },
    "poweredBy": {
      "bedrock": "Powered by Amazon Bedrock with tool use when configured.",
      "rules": "Using rule-based routing until Bedrock is configured."
    },
    "tabs": {"conversation": "Conversation", "retention": "Retention queue"},
    "empty": {"hint": "Try: “Show the product heatmap” or “Who is at highest churn risk?”"},
    "turn": {"user": "You", "assistant": "Copilot"},
    "source": {
      "bedrockTools": "· Bedrock + tools",
      "bedrock": "· Bedrock",
      "rules": "· Rules"
    },
    "input": {
      "label": "Ask Customer 360",
      "placeholder": "Ask about KPIs, customers, products… (Enter to send)"
    },
    "send": {"thinking": "Thinking…", "submit": "Ask"},
    "a11y": {"toggleClose": "Close executive copilot", "toggleOpen": "Open executive copilot"},
    "toggleTitle": {"close": "Close copilot", "open": "Open copilot"},
    "retention": {
      "showing": "Showing {{shown}} of {{total}} at-risk customers",
      "atRiskBook": "At risk {{atRisk}} · Book {{book}}",
      "openList": "Open full list in customer hub →"
    }
  },
  "charts": {
    "common": {
      "loading": "Loading…",
      "empty": "No data for this cohort yet.",
      "interactiveHint": "Click a point to drill into customers for that month.",
      "forecast": "(forecast)",
      "axisLeft": "· left",
      "axisRight": "· right"
    },
    "bookValue": {
      "title": "Book value",
      "subtitle": "Total customer value split by investments vs coverage & savings.",
      "totalBook": "Total book",
      "cohortTotalBook": "Cohort total book",
      "investments": "Investments",
      "coverageSavings": "Coverage & savings",
      "fullBookRef": "Full book (reference)"
    },
    "churnHorizon": {"title": "Churn horizon", "subtitle": "Projected value at risk by month (tier-weighted lapse)."},
    "investmentReturns": {"title": "Investment returns", "subtitle": "Average YTD return across investment snapshots."},
    "premiumMomentum": {
      "title": "Active policies & premium",
      "subtitle": "Premium base (left axis) and active policy count (right axis) — one customer may hold many policies."
    },
    "savingsAum": {
      "title": "Long-term savings (AUM)",
      "subtitle": "AUM (left) and savings policy count (right) — multiple policies per saver are normal."
    },
    "engagementObjective": {
      "title": "Customer engagement",
      "subtitle": "Digital & service touchpoints — customer at the center pillar."
    },
    "customerValue": {
      "title": "Customer value",
      "subtitle": "Solid lines are warehouse snapshots. Dashed projection: HIGH risk lapses to ₪0 within 3 months; MEDIUM extends recent history; LOW extends full history.",
      "loading": "Loading customer value…",
      "empty": "No value history for this customer.",
      "refreshing": "Refreshing chart…",
      "latestTotal": "Latest total",
      "vsStart": "vs start",
      "projected": "Projected",
      "lapseHigh": "HIGH tier lapse projection",
      "legendActual": "Actual total value",
      "legendProjected": "Projected (tier rules)"
    }
  }
}

HE = json.loads(json.dumps(EN))  # deep copy structure

def he_translate(obj):
    """Apply Hebrew strings — nested dict walk."""
    H = {
      "app.language": "שפה",
      "app.brand.title": "Insurance Customer 360",
      "app.brand.tagline": "Cloudera AI · תצוגות עסק ולקוח",
      "nav.workspace": "סביבת עבודה",
      "nav.business.title": "העסק",
      "nav.business.desc": "ספר, קohorts ו-KPIs של תיק",
      "nav.customer.title": "הלקוח",
      "nav.customer.desc": "פרופיל 360, תובנות ופנייה",
      "nav.engagement.title": "מעורבות",
      "nav.engagement.desc": "נקודות מגע, השפעה ופעולה הבאה",
      "nav.products.title": "מוצרים",
      "nav.products.desc": "מפת חום מוצרים ועומק לקוח",
      "nav.admin.section": "ניהול",
      "nav.admin.title": "נתונים וניהול",
      "nav.admin.desc": "בריאות, מחסן נתונים ומקור",
      "common.loading": "טוען…",
      "common.yes": "כן",
      "common.no": "לא",
      "common.none": "אין",
      "common.showAll": "הצג הכל",
      "errors.overviewLoadFailed": "טעינת סקירה נכשלה",
      "cohort.fullBook": "ספר מלא",
      "cohort.filteredCohort": "קohort מסונן",
      "copilot.title": "קopilot מנהלים",
      "copilot.shortTitle": "Copilot",
    }
    # Full Hebrew tree — key paths flattened for critical UI; rest filled below
    return obj

# Build HE with comprehensive translations
HE_TR = {
  "app": {
    "language": "שפה",
    "languageEn": "EN",
    "languageHe": "עב",
    "brand": {"title": "Insurance Customer 360", "tagline": "Cloudera AI · תצוגות עסק ולקוח"},
    "a11y": {"applicationAreas": "אזורי יישום", "administrationNav": "ניהול"},
    "dataFreshness": {
      "label": "רעננות נתונים",
      "warehouse": "מחסן נתונים",
      "metricsCache": "מטמון מדדים",
      "portfolioCache": "מטמון תיק",
      "churnScores": "ציוני נטישה",
      "churnScored": "{{date}} ({{count}} לקוחות)"
    }
  },
  "nav": {
    "workspace": "סביבת עבודה",
    "business": {"title": "העסק", "desc": "ספר, קohorts ומדדי תיק"},
    "customer": {"title": "הלקוח", "desc": "פרופיל 360, תובנות ופנייה"},
    "engagement": {"title": "מעורבות", "desc": "נקודות מגע, השפעה והפעולה הבאה", "short": "מעורבות"},
    "products": {"title": "מוצרים", "desc": "מפת חום מוצרים ועומק לקוח"},
    "admin": {"section": "ניהול", "title": "נתונים וניהול", "desc": "בריאות, מחסן ומקור נתונים"}
  },
  "common": {
    "loading": "טוען…",
    "yes": "כן",
    "no": "לא",
    "none": "אין",
    "showAll": "הצג הכל",
    "emDash": "—",
    "a11y": {"breadcrumb": "פירורי לחם"}
  },
  "errors": {
    "overviewLoadFailed": "טעינת הסקירה נכשלה",
    "productsLoadFailed": "טעינת המוצרים נכשלה",
    "engagementLoadFailed": "טעינת מרכז המעורבות נכשלה",
    "adminLoadFailed": "טעינת נתוני הניהול נכשלה",
    "customersLoadFailed": "טעינת הלקוחות נכשלה",
    "invalidCustomerId": "מזהה לקוח לא תקין",
    "customerNotFound": "הלקוח לא נמצא",
    "copilotUnreachable": "לא ניתן להגיע ל-copilot. ודא שה-API פועל.",
    "boundary": {
      "title": "משהו השתבש",
      "hint": "נסה רענון מלא. אם הבעיה נמשכת, הפעל מחדש את האפליקציה וודא ש-frontend/dist תואם לגרסת ה-API.",
      "reload": "טען מחדש"
    }
  },
  "cohort": {
    "fullBook": "ספר מלא",
    "filteredCohort": "קohort מסונן",
    "filteredBy": "מסונן לפי \"{{label}}\"",
    "fullActiveBook": "ספר לקוחות פעיל מלא",
    "segments": {
      "customers_all": "כל הלקוחות",
      "with_policies": "עם פוליסות",
      "with_foreclosures": "עם עיקולים",
      "with_investments": "עם השקעות",
      "with_insurance_status": "עם סטטוס ביטוח",
      "with_market_products": "עם מוצרי שוק"
    }
  },
  "business": EN["business"],  # placeholder — merge Hebrew below
}

# Merge Hebrew business section properly
HE_TR["business"] = {
  "domainFilter": {
    "helperAnalytics": "לחץ על כרטיס לסינון אנליטיקה. לחץ שוב לניקוי.",
    "helperCustomerList": "לחץ על כרטיס לסינון רשימת הלקוחות. לחץ שוב לניקוי.",
    "refreshedAt": "ספירות עודכנו {{time}}",
    "policyFoot": "{{active}} פעילות · ממוצע {{avg}} / לקוח",
    "allBookFoot": "{{policies}} פוליסות · {{active}} פעילות"
  },
  "compare": {
    "label": "השווה ל",
    "none": "ללא השוואה",
    "loading": "טוען cohort להשוואה…",
    "panelTitle": "השוואת cohort",
    "panelLede": "KPIs זה לצד זה עבור הכרטיס שנבחר מול cohort שני (הגרפים למעלה נשארים על הבחירה הראשית).",
    "metric": "מדד",
    "delta": "הפרש",
    "deltaVsCompare": "{{sign}}{{pct}}% מול השוואה",
    "deltaPts": "{{pts}} נק'"
  },
  "cohort": {
    "filteredBadge": "קohort מסונן",
    "vsBookLead": "פרוסה זו היא {{share}} מערך הלקוח הכולל בספר המלא (התייחסות למטה).",
    "shareOfBook": "{{pct}}% מהספר"
  },
  "portfolio": {
    "sectionGrowth": "צמיחת ספר ותחזית נטישה",
    "ledeFiltered": "{{caption}} — KPIs וגרפים מתעדכנים כשמשנים את כרטיסי הסקירה למעלה.",
    "ledeFull": "KPIs תיק עם תחזית נטישה מיושרת לתעשייה על ערך לקוח כולל.",
    "bookHistory": "היסטוריית ספר: {{range}}.",
    "mobileLead": "{{caption}} · סטטוס benchmark בכל כרטיס",
    "objectivesTitle": "מגמות יעדים אסטרטגיים",
    "objectivesDefaultNote": "מגמות הממופות לצמיחת חיסכון ארוכת טווח, מומנטום פרמיה ומעורבות לקוחות.",
    "updating": "מעדכן אנליטיקה…",
    "retentionRunScoring": "הרץ ציון נטישה להערכת שיעור lapse בתיק.",
    "retentionSub": "Lapse משוקלל 12 חוד' {{pct}}% · HIGH {{high}} · MED {{med}} · LOW {{low}}",
    "valueAtRiskSub": "Σ ערך לקוח × הסתברות lapse (משקל tier כשאין ציון ML)",
    "policyRecordsSub": "{{active}} פעילות · ממוצע {{avg}} / לקוח",
    "highRiskShareSub": "{{count}} לקוחות בסיכון גבוה",
    "retentionQueueHint": "פתח תור retention ב-copilot →",
    "kpi": {
      "totalBookValue": "ערך ספר כולל",
      "retentionForecast": "שימור 12 ח' (תחזית)",
      "valueAtChurnRisk": "ערך בסיכון נטישה",
      "activeCustomers": "לקוחות פעילים",
      "policyRecords": "רשומות פוליסה",
      "avgCustomerValue": "ערך לקוח ממוצע",
      "highRiskBookShare": "נתח ספר בסיכון גבוה",
      "bookGrowthHistory": "צמיחת ספר (היסטוריה)"
    }
  },
  "kpi": {
    "objective": "יעד: {{target}}",
    "thermo": {
      "atOrBelow": "ביעד או מתחת",
      "ofLimit": "{{pct}}% מהמגבלה",
      "ofObjective": "{{pct}}% מהיעד",
      "a11y": "{{status}} — {{detail}}"
    }
  },
  "compareRows": {
    "activeCustomers": "לקוחות פעילים",
    "totalBookValue": "ערך ספר כולל",
    "valueAtChurnRisk": "ערך בסיכון נטישה",
    "retentionForecast": "שימור 12 ח' (תחזית)"
  },
  "vsBookStats": {
    "customers": "לקוחות",
    "totalBookValue": "ערך ספר כולל",
    "policyRecords": "רשומות פוליסה",
    "avgCustomerValue": "ערך לקוח ממוצע"
  },
  "historyMonths": "{{first}} – {{last}} ({{count}} חודשים)"
}

HE_TR["mobile"] = {
  "backToCopilot": "← Copilot",
  "focusTitle": {
    "business": "KPIs עסק",
    "customers": "לקוחות",
    "customerProfile": "פרופיל לקוח",
    "products": "מוצרים",
    "engagement": "מעורבות",
    "admin": "ניהול",
    "details": "פרטים"
  }
}

HE_TR["copilot"] = {
  "title": "Copilot מנהלים",
  "shortTitle": "Copilot",
  "lede": {
    "phone": "שאל על הספר, ואז פתח קישור להתמקדות בעמוד בטלפון.",
    "desktop": "שאל על הספר; קישורים משנים את התצוגה הראשית או פותחים תור retention."
  },
  "poweredBy": {
    "bedrock": "מופעל על ידי Amazon Bedrock עם כלים כשמוגדר.",
    "rules": "ניתוב מבוסס כללים עד ש-Bedrock מוגדר."
  },
  "tabs": {"conversation": "שיחה", "retention": "תור retention"},
  "empty": {"hint": "נסה: \"הצג את מפת החום של המוצרים\" או \"מי בסיכון נטישה הגבוה ביותר?\""},
  "turn": {"user": "אתה", "assistant": "Copilot"},
  "source": {"bedrockTools": "· Bedrock + כלים", "bedrock": "· Bedrock", "rules": "· כללים"},
  "input": {"label": "שאל את Customer 360", "placeholder": "שאל על KPIs, לקוחות, מוצרים… (Enter לשליחה)"},
  "send": {"thinking": "חושב…", "submit": "שאל"},
  "a11y": {"toggleClose": "סגור copilot מנהלים", "toggleOpen": "פתח copilot מנהלים"},
  "toggleTitle": {"close": "סגור copilot", "open": "פתח copilot"},
  "retention": {
    "showing": "מציג {{shown}} מתוך {{total}} לקוחות בסיכון",
    "atRiskBook": "בסיכון {{atRisk}} · ספר {{book}}",
    "openList": "פתח רשימה מלאה במרכז הלקוח →"
  }
}

HE_TR["charts"] = {
  "common": {
    "loading": "טוען…",
    "empty": "אין נתונים ל-cohort זה עדיין.",
    "interactiveHint": "לחץ על נקודה לעומק לקוחות לחודש זה.",
    "forecast": "(תחזית)",
    "axisLeft": "· שמאל",
    "axisRight": "· ימין"
  },
  "bookValue": {
    "title": "ערך ספר",
    "subtitle": "ערך לקוח כולל מפוצל להשקעות מול כיסוי וחיסכון.",
    "totalBook": "ספר כולל",
    "cohortTotalBook": "ספר cohort כולל",
    "investments": "השקעות",
    "coverageSavings": "כיסוי וחיסכון",
    "fullBookRef": "ספר מלא (התייחסות)"
  },
  "churnHorizon": {"title": "אופק נטישה", "subtitle": "ערך בסיכון חזוי לפי חודש (lapse משוקלל tier)."},
  "investmentReturns": {"title": "תשואות השקעה", "subtitle": "תשואה YTD ממוצעת על צילומי השקעה."},
  "premiumMomentum": {
    "title": "פוליסות פעילות ופרמיה",
    "subtitle": "בסיס פרמיה (ציר שמאל) ומספר פוליסות פעילות (ציר ימין) — לקוח אחד יכול להחזיק פוליסות רבות."
  },
  "savingsAum": {
    "title": "חיסכון ארוך טווח (AUM)",
    "subtitle": "AUM (שמאל) ומספר פוליסות חיסכון (ימין) — מספר פוליסות לחוסך הוא תקין."
  },
  "engagementObjective": {
    "title": "מעורבות לקוחות",
    "subtitle": "נקודות מגע דיגיטליות ושירות — הלקוח במרכז."
  },
  "customerValue": {
    "title": "ערך לקוח",
    "subtitle": "קווים רציפים הם צילומי מחסן. קו מקווקו: סיכון HIGH — lapse ל-₪0 תוך 3 חודשים; MEDIUM מאריך היסטוריה אחרונה; LOW מאריך היסטוריה מלאה.",
    "loading": "טוען ערך לקוח…",
    "empty": "אין היסטוריית ערך ללקוח זה.",
    "refreshing": "מרענן גרף…",
    "latestTotal": "סה\"כ אחרון",
    "vsStart": "מול התחלה",
    "projected": "חזוי",
    "lapseHigh": "תחזית lapse tier HIGH",
    "legendActual": "ערך כולל בפועל",
    "legendProjected": "חזוי (כללי tier)"
  }
}

# Extend EN/HE with customer, engagement, products, admin sections
EXTRA_EN = {
  "customer": {
    "recent": {"title": "Recently viewed"},
    "homeLink": "Customer home",
    "back": {"engagement": "← Back to engagement", "list": "← Back to customers", "business": "← Back to the business"},
    "link": {"engagementHub": "Back to engagement hub", "list": "Back to customer list", "businessPortfolio": "Portfolio in the business"},
    "mobile": {"summaryLine": "{{city}} · {{policies}} policies · {{value}}"},
    "churn": {"scoredAt": "Churn scored {{date}}", "notScored": "Not scored", "likelihoodTitle": "Churn likelihood {{pct}}"},
    "privacyNotice": "City and last login are shown in full; other PII fields are masked in this demo.",
    "profile": {"type": "Type", "birthDate": "Birth date", "maritalStatus": "Marital status", "address": "Address", "communication": "Communication", "lastInteraction": "Last interaction"},
    "engagementHint": {"prefix": "Suggested from Engagement hub:"},
    "tabs": {"policies": "Policies", "foreclosures": "Foreclosures", "investments": "Investments", "interactions": "Interactions"},
    "policies": {
      "title": "Policies",
      "hint": "Click a policy to filter investment snapshots.",
      "columns": {"number": "Number", "type": "Type", "status": "Status", "active": "Active", "monthlyPremium": "Monthly premium"}
    },
    "foreclosures": {
      "title": "Foreclosures & encumbrances",
      "empty": "No foreclosure records.",
      "columns": {"proceeding": "Proceeding #", "amount": "Amount", "date": "Date", "portfolio": "Portfolio"}
    },
    "interactions": {
      "title": "Interaction timeline",
      "lede": "Synthetic omnichannel events from the warehouse engagement layer.",
      "stats": {"last90d": "Last 90 days: {{count}} events", "avgReview": "Avg review: {{avg}}/5", "openAgent": "Open agent items: {{count}}"},
      "empty": "No interaction events recorded.",
      "eventType": {"review": "Review", "agentQuestion": "Agent question", "webSearch": "Web search"},
      "signal": {"stars": "{{rating}}/5 stars", "resolved": "Resolved", "open": "Open", "helpSearch": "Help search", "productSearch": "Product search"}
    },
    "investments": {
      "title": "Latest investment snapshots",
      "policyFilter": "Policy filter:",
      "empty": "No investment snapshots for this selection.",
      "columns": {"policy": "Policy", "fund": "Fund", "snapshot": "Snapshot", "accumulation": "Accumulation", "ytdPl": "YTD P/L"}
    },
    "directory": {
      "title": "Customers",
      "titleCompact": "Matching customers",
      "chartFilter": {"prefix": "Chart snapshot:", "clear": "Clear date filter"},
      "cityFilter": {"prefix": "City:", "clear": "Clear city filter"},
      "productFilter": {"prefix": "Product filter: type {{code}}", "clear": "Clear product filter"},
      "cohortFilter": {"prefix": "Filter:", "clear": "Clear filter"},
      "allCohort": "Showing all current customers in this cohort",
      "sort": {
        "label": "Rank by",
        "options": {
          "churn_risk": "Churn, then value",
          "customer_value": "Value, then churn",
          "name": "Name (A–Z)",
          "policy_count": "Policy count",
          "investment_count": "Investment tracks"
        },
        "order": {
          "valueDesc": "Highest value first ↓",
          "valueAsc": "Lowest value first ↑",
          "riskDesc": "High risk first ↓",
          "riskAsc": "Low risk first ↑",
          "defaultDesc": "Highest first ↓",
          "defaultAsc": "Lowest first ↑"
        }
      },
      "search": {"label": "Search", "placeholder": "Name or customer ID"},
      "view": {"label": "Layout", "grid": "Cards", "table": "Table"},
      "updating": "Updating cards/table…",
      "empty": "No matching customers",
      "pagination": {
        "summaryAll": "Showing all {{total}} customers",
        "summaryRange": "Showing {{from}}–{{to}} of {{total}}",
        "perPage": "Per page",
        "previous": "Previous",
        "next": "Next",
        "pageOf": "Page {{page}} of {{pages}}"
      }
    },
    "table": {
      "empty": "No customers match this filter.",
      "columns": {"name": "Name", "city": "City", "value": "Value", "churn": "Churn", "policies": "Policies", "investments": "Investments", "lastLogin": "Last login"}
    },
    "card": {
      "rankA11y": "Rank {{rank}}",
      "value": "Customer value",
      "policies": "Policies",
      "investments": "Investments",
      "lastLogin": "Last login",
      "a11ySummary": "Customer summary"
    },
    "insights": {
      "title": "AI insights & next best action",
      "refresh": "Refresh insights",
      "loadingBedrock": "Calling Amazon Bedrock with this customer's warehouse and interaction data…",
      "loadingLocal": "Generating guidance with the built-in local advisor (Bedrock is not configured).",
      "idleHint": "Actionable recommendations can open a draft from account data; send is simulated in this demo.",
      "bedrockGenerated": "These insights were generated by Amazon Bedrock{{model}} from this customer's profile, policies, interactions, and churn score.",
      "fallbackReason": "Bedrock is configured but this response used the local advisor. Reason: {{reason}}",
      "fallbackGeneric": "Showing the local advisor for this response — Bedrock did not return a usable answer. Try Refresh insights.",
      "localOnly": "Showing the built-in local advisor. Configure AWS credentials and CUSTOMER360_BEDROCK_* variables to use Amazon Bedrock.",
      "loadError": "Could not load insights",
      "focusChurn": "Churn focus",
      "bedrockModelTitle": "Bedrock model ID"
    },
    "outreach": {
      "title": "Draft outreach",
      "disclaimer": "Send is simulated — no message leaves this browser.",
      "to": "To",
      "email": "Email",
      "phone": "Phone",
      "channel": "Channel",
      "subject": "Subject",
      "body": "Body",
      "cancel": "Cancel",
      "send": "Send (simulated)",
      "sent": "Simulated send recorded."
    }
  },
  "engagement": {
    "title": "Engagement & touchpoints",
    "lede": "Prioritize customers with the highest propensity to influence outcomes — ranked for outreach.",
    "domainFilter": {"helper": "Optional cohort filter (same cards as The business)."},
    "summary": {
      "touchpoints90": {"label": "Touchpoints (90d)", "sub": "{{count}} customers active"},
      "digital90": {"label": "Digital & agent", "sub": "Web searches & agent questions"},
      "reviews90": {"label": "Reviews (90d)", "sub": "Voice-of-customer events"},
      "openAgent": {"label": "Open agent questions", "sub": "Needs resolution in 90d window"}
    },
    "list": {
      "title": "Influence priority list",
      "titleMobile": "Top outreach",
      "lede": "Ranked by influence score (propensity × value). Showing {{shown}} of {{total}}.",
      "empty": "No engagement opportunities match this filter.",
      "bookSuffix": "{{value}} book"
    },
    "loading": "Loading engagement opportunities…",
    "influence": {"label": "Influence"},
    "a11y": {"influenceTitle": "Propensity to influence"},
    "touchpoints": {
      "count90": "{{count}} touchpoints (90d)",
      "webSearches": "{{count}} web searches",
      "reviews": "{{count}} reviews",
      "openQuestions": "{{count}} open questions",
      "daysSince": "{{days}}d since last touch"
    },
    "action": {"recommendedLabel": "Recommended next step", "actChannel": "Act — {{channel}}", "viewTouchpoints": "View touchpoints"},
    "channel": {"email": "Email", "phone": "Phone", "sms": "SMS"}
  },
  "products": {
    "lede": "Policy products grouped by class — cell intensity reflects customer count in the selected cohort.",
    "mobile": {"title": "Top products"},
    "filter": {"banner": "Showing {{segment}}{{city}}", "clear": "Clear filters"},
    "legend": {"highest": "Highest uptake", "strong": "Strong", "moderate": "Moderate", "lighter": "Lighter"},
    "a11y": {"legend": "Customer count intensity"},
    "filters": {"cohort": "Customer cohort", "city": "City", "allCities": "All cities"},
    "loading": "Loading product catalog…",
    "customersCount": "{{count}} customers",
    "activePoliciesCount": "{{count}} active policies",
    "classStats": "{{customers}} customers · {{policies}} policies",
    "empty": "No policy products in the warehouse."
  },
  "admin": {
    "mobile": {
      "snapshotTitle": "Warehouse snapshot",
      "flags": "Quality flags:",
      "healthFlags": "Health flags:",
      "desktopHint": "Open desktop view for schema map and KPI benchmarks."
    },
    "title": "Warehouse & data admin",
    "lede": "Table inventory, load timestamps, completeness checks, and configuration for KPI objectives.",
    "loading": "Loading admin metadata…",
    "health": {
      "title": "System health",
      "lede": "Runtime checks for API, warehouse connectivity, caches, and churn scoring freshness.",
      "attentionNote": "{{count}} check(s) need attention (warn or critical)."
    },
    "kpi": {
      "databaseFile": {"label": "Database file"},
      "warehouseLoaded": {"label": "Warehouse last loaded"},
      "cataloguedTables": {"label": "Catalogued tables"},
      "qualityFlags": {"label": "Quality flags", "sub": "Non-OK completeness checks"}
    },
    "tables": {
      "title": "Table overview",
      "lede": "Row counts are live from the configured warehouse backend.",
      "columns": {"table": "Table", "layer": "Layer", "domain": "Domain", "rows": "Rows", "lastLoaded": "Last loaded", "sourceJob": "Source job"}
    },
    "schema": {
      "title": "Schema map",
      "lede": "Each card lists live SQLite columns for demo tables; join reference shows relationships.",
      "joinReference": "Join reference",
      "joinColumns": {"from": "From", "to": "To", "join": "Join", "cardinality": "Cardinality"}
    },
    "quality": {"title": "Completeness & quality"},
    "config": {
      "title": "Configuration",
      "lede": "Warehouse connectivity and business KPI objectives used on The business page.",
      "a11y": "Admin configuration",
      "tabs": {"warehouse": "Warehouse backend", "kpiBenchmarks": "Business KPI benchmarks"}
    },
    "datasource": {
      "title": "Warehouse backend",
      "modeLegend": "Backend mode",
      "sqlite": "SQLite file (demo)",
      "trino": "Trino / Iceberg",
      "sqlitePath": "SQLite path",
      "trinoHost": "Trino JDBC URL",
      "catalog": "Catalog",
      "schema": "Schema",
      "icebergRest": "Iceberg REST catalog URL",
      "save": "Save configuration",
      "saving": "Saving…",
      "saved": "Configuration saved.",
      "error": "Could not save configuration",
      "lastUpdated": "Last updated {{date}}"
    },
    "kpiBenchmarks": {
      "title": "Business KPI benchmarks",
      "lede": "Targets shown on portfolio KPI cards (thermometer and objective line).",
      "columns": {"kpi": "KPI", "target": "Target", "unit": "Unit", "direction": "Direction", "preview": "Preview"},
      "help": "Values are stored in admin metadata and applied on next portfolio load.",
      "preview": "Preview",
      "save": "Save benchmarks",
      "saving": "Saving…",
      "saved": "Benchmarks saved.",
      "placeholderAuto": "Auto"
    }
  }
}

def deep_merge(a, b):
    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(v, dict):
            deep_merge(a[k], v)
        else:
            a[k] = v

deep_merge(EN, EXTRA_EN)

# Hebrew extras — mirror structure with translations (abbreviated for script; copy EN then patch key sections)
EXTRA_HE = json.loads(json.dumps(EXTRA_EN))
# Patch major HE customer/engagement/products/admin strings
EXTRA_HE["customer"]["recent"]["title"] = "נצפו לאחרונה"
EXTRA_HE["customer"]["directory"]["title"] = "לקוחות"
EXTRA_HE["engagement"]["title"] = "מעורבות ונקודות מגע"
EXTRA_HE["products"]["lede"] = "מוצרי פוליסה מקובצים לפי class — עוצמת תא משקפת מספר לקוחות ב-cohort שנבחר."
EXTRA_HE["admin"]["title"] = "ניהול מחסן ונתונים"
deep_merge(HE_TR, EXTRA_HE)

ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / "en.json").write_text(json.dumps(EN, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(ROOT / "he.json").write_text(json.dumps(HE_TR, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Wrote", ROOT / "en.json", "and", ROOT / "he.json")
