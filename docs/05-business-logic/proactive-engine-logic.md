# Proactive Engine Logic Specification

## Overview

The Proactive Engine is the core differentiator of the platform, enabling AI-driven interventions based on user behavior analysis, engagement patterns, and coaching psychology principles. It proactively initiates conversations, provides timely support, and prevents user abandonment through intelligent trigger systems.

## Core Architecture

### Behavioral Analysis System
```javascript
class BehaviorAnalyzer {
  constructor() {
    this.engagementScorer = new EngagementScorer();
    this.patternDetector = new PatternDetector();
    this.riskAssessor = new RiskAssessor();
    this.motivationTracker = new MotivationTracker();
  }

  async analyzeBehavior(userId, timeWindow = '7d') {
    const userActivity = await this.getUserActivity(userId, timeWindow);
    const conversationHistory = await this.getConversationHistory(userId, timeWindow);
    const progressData = await this.getProgressData(userId, timeWindow);

    return {
      engagementScore: this.engagementScorer.calculate(userActivity),
      behaviorPatterns: this.patternDetector.identify(userActivity),
      abandonmentRisk: this.riskAssessor.assess(userActivity, conversationHistory),
      motivationLevel: this.motivationTracker.evaluate(conversationHistory, progressData),
      interventionRecommendations: this.generateInterventionRecommendations(userActivity)
    };
  }
}
```

### Engagement Scoring Algorithm
```javascript
class EngagementScorer {
  calculate(userActivity) {
    const weights = {
      messageFrequency: 0.25,
      responseTime: 0.20,
      sessionDuration: 0.15,
      habitCompletion: 0.20,
      contentInteraction: 0.10,
      proactiveInitiation: 0.10
    };

    const scores = {
      messageFrequency: this.scoreMessageFrequency(userActivity.messages),
      responseTime: this.scoreResponseTime(userActivity.responses),
      sessionDuration: this.scoreSessionDuration(userActivity.sessions),
      habitCompletion: this.scoreHabitCompletion(userActivity.habits),
      contentInteraction: this.scoreContentInteraction(userActivity.content),
      proactiveInitiation: this.scoreProactiveInitiation(userActivity.proactive)
    };

    const weightedScore = Object.keys(weights).reduce((total, metric) => {
      return total + (scores[metric] * weights[metric]);
    }, 0);

    return {
      overall: Math.round(weightedScore * 100) / 100,
      breakdown: scores,
      trend: this.calculateTrend(userActivity),
      lastUpdated: new Date()
    };
  }

  scoreMessageFrequency(messages) {
    const dailyAverage = messages.length / 7;
    // Optimal range: 2-5 messages per day
    if (dailyAverage >= 2 && dailyAverage <= 5) return 1.0;
    if (dailyAverage >= 1 && dailyAverage < 2) return 0.7;
    if (dailyAverage > 5 && dailyAverage <= 8) return 0.8;
    if (dailyAverage < 1) return 0.3;
    return 0.5; // Too many messages might indicate frustration
  }

  scoreResponseTime(responses) {
    const averageResponseTime = responses.reduce((sum, r) => sum + r.responseTimeMinutes, 0) / responses.length;
    // Optimal: within 2 hours
    if (averageResponseTime <= 120) return 1.0;
    if (averageResponseTime <= 480) return 0.8; // 8 hours
    if (averageResponseTime <= 1440) return 0.6; // 24 hours
    return 0.3;
  }
}
```

## Trigger System Architecture

### Trigger Types and Conditions
```javascript
const TriggerTypes = {
  INACTIVITY: {
    name: "Inactivity Detection",
    conditions: {
      no_messages: { threshold: 24, unit: "hours" },
      no_habit_completion: { threshold: 48, unit: "hours" },
      no_app_usage: { threshold: 72, unit: "hours" }
    },
    priority: "medium",
    cooldown: { duration: 12, unit: "hours" }
  },

  PROGRESS_STAGNATION: {
    name: "Progress Stagnation",
    conditions: {
      no_goal_progress: { threshold: 7, unit: "days" },
      declining_completion_rate: { threshold: 0.3, comparison: "below_average" },
      repeated_failures: { threshold: 3, consecutive: true }
    },
    priority: "high",
    cooldown: { duration: 24, unit: "hours" }
  },

  MOTIVATION_DROP: {
    name: "Motivation Level Drop",
    conditions: {
      engagement_score_drop: { threshold: 0.2, timeframe: "3d" },
      negative_sentiment: { threshold: 0.6, consecutive_messages: 2 },
      goal_abandonment_signals: { keywords: ["give up", "too hard", "impossible"] }
    },
    priority: "high",
    cooldown: { duration: 6, unit: "hours" }
  },

  MILESTONE_APPROACH: {
    name: "Milestone Approaching",
    conditions: {
      days_until_milestone: { threshold: 1, unit: "days" },
      progress_percentage: { min: 0.8, max: 0.95 },
      completion_probability: { threshold: 0.7 }
    },
    priority: "low",
    cooldown: { duration: 48, unit: "hours" }
  },

  STREAK_BREAK: {
    name: "Streak Break Risk",
    conditions: {
      current_streak: { min: 7, unit: "days" },
      time_since_last_activity: { threshold: 18, unit: "hours" },
      historical_break_pattern: { risk_score: 0.6 }
    },
    priority: "medium",
    cooldown: { duration: 8, unit: "hours" }
  }
};
```

### Trigger Evaluation Engine
```javascript
class TriggerEvaluator {
  constructor() {
    this.conditionEvaluators = new Map();
    this.setupConditionEvaluators();
  }

  async evaluateAllTriggers(userId) {
    const userContext = await this.getUserContext(userId);
    const activeTriggers = [];

    for (const [triggerType, config] of Object.entries(TriggerTypes)) {
      const evaluation = await this.evaluateTrigger(triggerType, config, userContext);
      
      if (evaluation.shouldTrigger) {
        activeTriggers.push({
          type: triggerType,
          priority: config.priority,
          confidence: evaluation.confidence,
          context: evaluation.context,
          recommendedAction: evaluation.recommendedAction
        });
      }
    }

    return this.prioritizeTriggers(activeTriggers);
  }

  async evaluateTrigger(triggerType, config, userContext) {
    const conditions = config.conditions;
    const evaluationResults = [];

    for (const [conditionName, conditionConfig] of Object.entries(conditions)) {
      const evaluator = this.conditionEvaluators.get(conditionName);
      if (evaluator) {
        const result = await evaluator.evaluate(conditionConfig, userContext);
        evaluationResults.push(result);
      }
    }

    const shouldTrigger = this.combineConditionResults(evaluationResults);
    const confidence = this.calculateConfidence(evaluationResults);

    return {
      shouldTrigger,
      confidence,
      context: this.buildTriggerContext(evaluationResults, userContext),
      recommendedAction: this.determineRecommendedAction(triggerType, evaluationResults)
    };
  }
}
```

### Abandonment Prevention Logic
```javascript
class AbandonmentPredictor {
  constructor() {
    this.model = new AbandonmentPredictionModel();
    this.riskFactors = this.initializeRiskFactors();
  }

  async predictAbandonmentRisk(userId) {
    const features = await this.extractFeatures(userId);
    const riskScore = await this.model.predict(features);
    const riskFactors = this.identifyRiskFactors(features);

    return {
      riskScore: riskScore, // 0-1 scale
      riskLevel: this.categorizeRisk(riskScore),
      primaryRiskFactors: riskFactors,
      interventionRecommendations: this.generateInterventions(riskScore, riskFactors),
      confidenceInterval: this.calculateConfidenceInterval(features)
    };
  }

  async extractFeatures(userId) {
    const userActivity = await this.getUserActivity(userId, '14d');
    const userProfile = await this.getUserProfile(userId);
    const conversationHistory = await this.getConversationHistory(userId, '7d');

    return {
      // Engagement features
      messageFrequency: this.calculateMessageFrequency(userActivity),
      responseLatency: this.calculateAverageResponseTime(conversationHistory),
      sessionDuration: this.calculateAverageSessionDuration(userActivity),
      
      // Progress features
      goalCompletionRate: this.calculateGoalCompletionRate(userActivity),
      habitConsistency: this.calculateHabitConsistency(userActivity),
      progressVelocity: this.calculateProgressVelocity(userActivity),
      
      // Behavioral features
      timeOfDayPatterns: this.analyzeTimePatterns(userActivity),
      weekdayVsWeekend: this.analyzeWeekPatterns(userActivity),
      interactionInitiation: this.analyzeInitiationPatterns(conversationHistory),
      
      // Sentiment features
      messageSentiment: this.analyzeSentiment(conversationHistory),
      frustrationIndicators: this.detectFrustration(conversationHistory),
      motivationLevel: this.assessMotivation(conversationHistory),
      
      // Profile features
      userGoals: userProfile.goals,
      experienceLevel: userProfile.experienceLevel,
      demographicFactors: this.extractDemographics(userProfile)
    };
  }

  generateInterventions(riskScore, riskFactors) {
    const interventions = [];

    if (riskScore > 0.7) {
      interventions.push({
        type: "immediate_human_outreach",
        priority: "high",
        message: "Personal check-in from creator",
        timing: "within_2_hours"
      });
    }

    if (riskFactors.includes("low_engagement")) {
      interventions.push({
        type: "engagement_boost",
        priority: "medium", 
        message: "Gamification and achievement focus",
        timing: "next_interaction"
      });
    }

    if (riskFactors.includes("goal_mismatch")) {
      interventions.push({
        type: "goal_realignment",
        priority: "high",
        message: "Goal setting conversation",
        timing: "within_24_hours"
      });
    }

    return interventions;
  }
}
```

## Message Generation Logic

### Proactive Message Templates
```javascript
const ProactiveMessageTemplates = {
  INACTIVITY_FOLLOWUP: {
    casual: [
      "Hey {user_name}! I noticed you haven't checked in for a while. How are things going? 😊",
      "Hi there! Just wanted to see how you're doing with your {primary_goal}. Any challenges I can help with?",
      "Thinking of you! How has your week been going with the habits we've been working on?"
    ],
    supportive: [
      "Hi {user_name}, I wanted to reach out because I care about your progress. Sometimes life gets busy - how can I support you right now?",
      "No judgment here! I know staying consistent can be challenging. What's been the biggest obstacle lately?",
      "You've made such great progress with {recent_achievement}. What would help you get back on track?"
    ],
    motivational: [
      "Remember why you started this journey, {user_name}! Your goal of {primary_goal} is still within reach. Ready to take the next step?",
      "Every expert was once a beginner. You've already proven you can do this - let's keep that momentum going! 💪",
      "I believe in you! Sometimes we just need a gentle reminder of how capable we are. What's one small thing you can do today?"
    ]
  },

  PROGRESS_CELEBRATION: {
    milestone_reached: [
      "🎉 Incredible! You just reached {milestone_name}! This is a huge accomplishment - you should be proud!",
      "WOW! {milestone_name} achieved! 🏆 You're proving to yourself that you can do anything you set your mind to!",
      "This is amazing, {user_name}! Reaching {milestone_name} shows your dedication is paying off. How does it feel?"
    ],
    streak_celebration: [
      "🔥 {streak_count} days in a row! You're on fire! This consistency is exactly what creates lasting change.",
      "Look at you go! {streak_count} consecutive days of {habit_name}. You're building an incredible habit!",
      "Streak alert! 🚨 {streak_count} days strong! Your future self is going to thank you for this consistency."
    ]
  },

  MOTIVATION_BOOST: {
    gentle_encouragement: [
      "Progress isn't always linear, and that's perfectly okay. You're learning and growing with every step. 🌱",
      "Some days are harder than others, and that's part of the journey. What matters is that you don't give up on yourself.",
      "Remember: you don't have to be perfect, you just have to be persistent. You've got this! 💙"
    ],
    challenge_reframe: [
      "What if we looked at this challenge as your growth edge? It's showing you exactly where you're expanding! 🚀",
      "Every obstacle is actually information about what you need to learn next. What is this situation teaching you?",
      "The fact that you're facing this challenge means you're pushing beyond your comfort zone. That's where the magic happens!"
    ]
  }
};
```

### Dynamic Message Personalization
```javascript
class MessagePersonalizer {
  constructor() {
    this.sentimentAnalyzer = new SentimentAnalyzer();
    this.contextBuilder = new ContextBuilder();
    this.templateEngine = new TemplateEngine();
  }

  async personalizeMessage(template, userContext, triggerContext) {
    const personalizationData = await this.buildPersonalizationData(userContext, triggerContext);
    const selectedTemplate = this.selectOptimalTemplate(template, userContext);
    const personalizedMessage = this.templateEngine.render(selectedTemplate, personalizationData);
    
    return {
      message: personalizedMessage,
      personalizationScore: this.calculatePersonalizationScore(personalizationData),
      expectedEngagement: this.predictEngagement(personalizedMessage, userContext),
      alternatives: this.generateAlternatives(template, personalizationData)
    };
  }

  async buildPersonalizationData(userContext, triggerContext) {
    return {
      // Basic user data
      user_name: userContext.profile.name || "there",
      primary_goal: userContext.goals[0]?.name || "your goals",
      
      // Progress data
      recent_achievement: await this.getRecentAchievement(userContext.userId),
      current_streak: await this.getCurrentStreak(userContext.userId),
      completion_rate: await this.getCompletionRate(userContext.userId),
      
      // Behavioral insights
      preferred_communication_style: userContext.preferences.communicationStyle,
      optimal_message_length: userContext.preferences.messageLength,
      emoji_preference: userContext.preferences.emojiUsage,
      
      // Contextual data
      time_of_day: this.getTimeOfDay(),
      day_of_week: this.getDayOfWeek(),
      season: this.getSeason(),
      
      // Trigger-specific data
      trigger_reason: triggerContext.reason,
      days_since_last_interaction: triggerContext.daysSinceLastInteraction,
      risk_factors: triggerContext.riskFactors
    };
  }

  selectOptimalTemplate(templates, userContext) {
    const userStyle = userContext.preferences.communicationStyle;
    const motivationLevel = userContext.currentMotivationLevel;
    
    // Select template category based on user state
    if (motivationLevel < 0.4) {
      return templates.supportive || templates.gentle_encouragement;
    } else if (motivationLevel > 0.7) {
      return templates.motivational || templates.challenge_reframe;
    } else {
      return templates.casual || templates[Object.keys(templates)[0]];
    }
  }
}
```

## Timing Optimization

### Optimal Timing Predictor
```javascript
class TimingOptimizer {
  constructor() {
    this.userActivityAnalyzer = new UserActivityAnalyzer();
    this.responseRatePredictor = new ResponseRatePredictor();
    this.contextualFactors = new ContextualFactors();
  }

  async calculateOptimalTiming(userId, messageType, urgency = 'normal') {
    const userPatterns = await this.userActivityAnalyzer.getActivityPatterns(userId);
    const responseRates = await this.responseRatePredictor.getHistoricalRates(userId);
    const contextualData = await this.contextualFactors.getCurrentContext(userId);

    const candidates = this.generateTimingCandidates(userPatterns, messageType);
    const scoredCandidates = await this.scoreTimingCandidates(candidates, responseRates, contextualData);
    
    return this.selectOptimalTiming(scoredCandidates, urgency);
  }

  generateTimingCandidates(userPatterns, messageType) {
    const candidates = [];
    
    // Based on historical activity peaks
    userPatterns.activityPeaks.forEach(peak => {
      candidates.push({
        time: peak.time,
        confidence: peak.consistency,
        reason: "historical_activity_peak",
        score: peak.averageEngagement
      });
    });

    // Based on message type optimization
    const typeOptimalTimes = this.getMessageTypeOptimalTimes(messageType);
    typeOptimalTimes.forEach(time => {
      candidates.push({
        time: time.hour,
        confidence: time.effectiveness,
        reason: "message_type_optimization",
        score: time.averageResponseRate
      });
    });

    // Based on day-of-week patterns
    const dayPatterns = this.getDayOfWeekPatterns(userPatterns);
    dayPatterns.forEach(pattern => {
      candidates.push({
        time: pattern.optimalTime,
        confidence: pattern.consistency,
        reason: "day_of_week_pattern",
        score: pattern.engagementRate
      });
    });

    return candidates;
  }

  async scoreTimingCandidates(candidates, responseRates, contextualData) {
    return candidates.map(candidate => {
      const baseScore = candidate.score;
      const contextualMultiplier = this.calculateContextualMultiplier(candidate.time, contextualData);
      const responseRateBonus = this.getResponseRateBonus(candidate.time, responseRates);
      
      return {
        ...candidate,
        finalScore: baseScore * contextualMultiplier + responseRateBonus,
        contextualFactors: contextualData,
        adjustments: {
          contextualMultiplier,
          responseRateBonus
        }
      };
    });
  }
}
```

### Intervention Scheduling
```javascript
class InterventionScheduler {
  constructor() {
    this.timingOptimizer = new TimingOptimizer();
    this.messageQueue = new MessageQueue();
    this.conflictResolver = new ConflictResolver();
  }

  async scheduleIntervention(intervention, userId) {
    const optimalTiming = await this.timingOptimizer.calculateOptimalTiming(
      userId, 
      intervention.type, 
      intervention.urgency
    );

    const scheduledTime = this.adjustForConstraints(optimalTiming, intervention);
    const queuePosition = await this.messageQueue.schedule(intervention, scheduledTime);

    // Check for conflicts with existing scheduled messages
    const conflicts = await this.conflictResolver.checkConflicts(userId, scheduledTime);
    if (conflicts.length > 0) {
      const resolvedTime = await this.conflictResolver.resolve(conflicts, intervention);
      return this.rescheduleIntervention(intervention, resolvedTime);
    }

    return {
      interventionId: intervention.id,
      scheduledFor: scheduledTime,
      queuePosition: queuePosition,
      estimatedDelivery: this.calculateEstimatedDelivery(scheduledTime),
      canCancel: true,
      canReschedule: true
    };
  }

  adjustForConstraints(optimalTiming, intervention) {
    let adjustedTime = optimalTiming.recommendedTime;

    // Respect user's do-not-disturb hours
    if (this.isInDoNotDisturbHours(adjustedTime, intervention.userId)) {
      adjustedTime = this.findNextAvailableTime(adjustedTime, intervention.userId);
    }

    // Apply minimum interval between messages
    const lastMessageTime = this.getLastMessageTime(intervention.userId);
    const minInterval = this.getMinimumInterval(intervention.type);
    if (adjustedTime - lastMessageTime < minInterval) {
      adjustedTime = lastMessageTime + minInterval;
    }

    // Consider urgency adjustments
    if (intervention.urgency === 'high') {
      adjustedTime = Math.min(adjustedTime, Date.now() + (30 * 60 * 1000)); // Max 30 min delay
    } else if (intervention.urgency === 'low') {
      adjustedTime = Math.max(adjustedTime, Date.now() + (2 * 60 * 60 * 1000)); // Min 2 hour delay
    }

    return adjustedTime;
  }
}
```

## Success Measurement and Optimization

### Intervention Effectiveness Tracking
```javascript
class EffectivenessTracker {
  constructor() {
    this.metricsCollector = new MetricsCollector();
    this.outcomeAnalyzer = new OutcomeAnalyzer();
    this.feedbackProcessor = new FeedbackProcessor();
  }

  async trackInterventionOutcome(interventionId, timeWindow = '48h') {
    const intervention = await this.getIntervention(interventionId);
    const userActivity = await this.getUserActivityAfterIntervention(
      intervention.userId, 
      intervention.deliveredAt, 
      timeWindow
    );

    const outcome = {
      interventionId: interventionId,
      userId: intervention.userId,
      type: intervention.type,
      deliveredAt: intervention.deliveredAt,
      
      // Immediate response metrics
      userResponded: userActivity.hasResponse,
      responseTime: userActivity.responseTime,
      responseLength: userActivity.responseLength,
      responseSentiment: userActivity.responseSentiment,
      
      // Behavioral change metrics
      activityIncrease: this.calculateActivityIncrease(userActivity),
      goalProgressMade: this.calculateGoalProgress(userActivity),
      habitCompletionImprovement: this.calculateHabitImprovement(userActivity),
      
      // Engagement metrics
      sessionDurationChange: this.calculateSessionDurationChange(userActivity),
      messageFrequencyChange: this.calculateMessageFrequencyChange(userActivity),
      proactiveEngagement: this.calculateProactiveEngagement(userActivity),
      
      // Long-term impact
      retentionImpact: await this.calculateRetentionImpact(intervention.userId, timeWindow),
      satisfactionChange: await this.calculateSatisfactionChange(intervention.userId, timeWindow)
    };

    await this.storeOutcome(outcome);
    await this.updateInterventionModel(outcome);
    
    return outcome;
  }

  async optimizeInterventionStrategy(creatorId, timeWindow = '30d') {
    const interventions = await this.getInterventions(creatorId, timeWindow);
    const outcomes = await this.getOutcomes(interventions.map(i => i.id));
    
    const analysis = {
      overallEffectiveness: this.calculateOverallEffectiveness(outcomes),
      bestPerformingTypes: this.identifyBestPerformingTypes(outcomes),
      optimalTiming: this.identifyOptimalTiming(outcomes),
      userSegmentInsights: this.analyzeUserSegments(outcomes),
      recommendations: this.generateOptimizationRecommendations(outcomes)
    };

    return analysis;
  }
}
```

This proactive engine logic provides the foundation for intelligent, behavior-driven interventions that can significantly improve user engagement, reduce abandonment, and enhance coaching outcomes through data-driven personalization and optimal timing.