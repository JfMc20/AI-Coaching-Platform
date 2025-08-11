# Mobile App User Experience Specification

## Overview

The "Compañero" mobile app provides end users with a personalized, branded coaching experience featuring habit tracking, gamification, progress visualization, and seamless AI-powered conversations. The app is designed to be the primary touchpoint for users to engage with their coaching programs.

## Design Philosophy

### Core Principles
1. **Personal Connection**: Every interaction feels personal and tailored to the user
2. **Habit-Centric Design**: Interface optimized for daily habit tracking and reinforcement
3. **Motivational Psychology**: Design elements that encourage and celebrate progress
4. **Seamless Coaching**: AI conversations feel natural and supportive
5. **Creator Branding**: Customizable to reflect each creator's unique brand
6. **Offline Capability**: Core features work without internet connection

## App Architecture

### Navigation Structure
```
Compañero App
├── Home (Dashboard & Today's Focus)
├── Chat (AI Coaching Conversations)
├── Progress (Tracking & Analytics)
├── Programs (Active & Available Programs)
├── Library (Content & Resources)
└── Profile (Settings & Achievements)
```

### Information Hierarchy
- **Primary**: Today's habits, active conversations, immediate actions
- **Secondary**: Progress trends, program overview, recent achievements
- **Tertiary**: Historical data, settings, archived content

## Onboarding Experience

### Welcome Flow (5 Screens)

#### Screen 1: Brand Introduction
```
┌─────────────────────────────────────┐
│                                     │
│         [Creator Logo/Avatar]       │
│                                     │
│    Welcome to Your Personal        │
│         Coaching Journey            │
│                                     │
│    "Hi! I'm Sarah, your fitness     │
│     and wellness coach. I'm here    │
│     to help you build sustainable   │
│     habits that transform your      │
│     life, one day at a time."       │
│                                     │
│                                     │
│              [Get Started]          │
│                                     │
└─────────────────────────────────────┘
```

#### Screen 2: Goal Setting
```
┌─────────────────────────────────────┐
│  ← Back        Goal Setting         │
├─────────────────────────────────────┤
│                                     │
│    What would you like to focus     │
│              on first?              │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │  🏃‍♀️ Build Exercise Habits      │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │  🥗 Improve Nutrition           │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │  😴 Better Sleep Routine        │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │  🧘‍♀️ Stress Management          │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │  📚 Personal Development        │ │
│  └─────────────────────────────────┘ │
│                                     │
│              [Continue]             │
└─────────────────────────────────────┘
```

#### Screen 3: Habit Preferences
```
┌─────────────────────────────────────┐
│  ← Back    Habit Preferences        │
├─────────────────────────────────────┤
│                                     │
│   How do you prefer to build        │
│            new habits?              │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🐌 Start small and build up     │ │
│  │    (Recommended for beginners)  │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ ⚡ Jump in with bigger changes  │ │
│  │    (For experienced habit       │ │
│  │     builders)                   │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🎯 Focus on one thing at a time │ │
│  │    (Recommended for busy        │ │
│  │     schedules)                  │ │
│  └─────────────────────────────────┘ │
│                                     │
│              [Continue]             │
└─────────────────────────────────────┘
```

#### Screen 4: Notification Preferences
```
┌─────────────────────────────────────┐
│  ← Back    Stay Connected           │
├─────────────────────────────────────┤
│                                     │
│    Let me help you stay on track    │
│        with gentle reminders       │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🔔 Daily habit reminders        │ │
│  │    [Toggle: ON]                 │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 💬 Motivational check-ins       │ │
│  │    [Toggle: ON]                 │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🎉 Progress celebrations        │ │
│  │    [Toggle: ON]                 │ │
│  └─────────────────────────────────┘ │
│                                     │
│  Best time for reminders:           │
│  [Morning ▼] at [9:00 AM ▼]        │
│                                     │
│              [Continue]             │
└─────────────────────────────────────┘
```

#### Screen 5: Ready to Start
```
┌─────────────────────────────────────┐
│           You're All Set!           │
├─────────────────────────────────────┤
│                                     │
│         [Success Animation]         │
│                                     │
│    Your personalized coaching       │
│      journey starts now!           │
│                                     │
│         Here's what's next:         │
│                                     │
│  ✅ I'll create your first habit    │
│  ✅ Set up your daily routine       │
│  ✅ Send you a welcome message      │
│                                     │
│    Remember: Small steps lead       │
│       to big transformations        │
│                                     │
│                                     │
│          [Start My Journey]         │
│                                     │
└─────────────────────────────────────┘
```

## Home Screen (Dashboard)

### Layout Structure
```
┌─────────────────────────────────────┐
│  Good morning, Alex! ☀️            │
│  Today is Day 12 of your journey    │
├─────────────────────────────────────┤
│           Today's Focus             │
│  ┌─────────────────────────────────┐ │
│  │ 🏃‍♀️ Morning Walk (20 min)       │ │
│  │ Status: Not started             │ │
│  │ ┌─────────────┐ ┌─────────────┐ │ │
│  │ │    Done     │ │    Skip     │ │ │
│  │ └─────────────┘ └─────────────┘ │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 💧 Drink Water (8 glasses)      │ │
│  │ Progress: ●●●●○○○○ (4/8)        │ │
│  │ ┌─────────────┐ ┌─────────────┐ │ │
│  │ │     +1      │ │   Details   │ │ │
│  │ └─────────────┘ └─────────────┘ │ │
│  └─────────────────────────────────┘ │
│                                     │
│         Quick Actions               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │   💬    │ │   📊    │ │   📚    │ │
│  │  Chat   │ │Progress │ │Library  │ │
│  └─────────┘ └─────────┘ └─────────┘ │
│                                     │
│         Recent Activity             │
│  🎉 Completed 7-day streak!         │
│  💬 New message from Sarah          │
│  🏆 Earned "Consistency" badge      │
└─────────────────────────────────────┘
```

### Habit Tracking Interface
```javascript
const HabitCard = {
  layout: "card",
  components: {
    header: {
      icon: "🏃‍♀️",
      title: "Morning Walk",
      subtitle: "20 minutes",
      streak: "12 days"
    },
    progress: {
      type: "binary", // or "incremental", "time-based"
      status: "pending", // "completed", "skipped"
      visualIndicator: "checkbox" // or "progress-bar", "counter"
    },
    actions: {
      primary: "Mark Done",
      secondary: "Skip Today",
      tertiary: "Edit Habit"
    },
    motivation: {
      message: "You're building an amazing streak!",
      encouragement: "Just 20 minutes to keep it going"
    }
  }
};
```

## Chat Interface

### Conversation Layout
```
┌─────────────────────────────────────┐
│  ← Back     💬 Sarah Johnson        │
│              🟢 Online              │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Hey Alex! I noticed you     │    │
│  │ completed your morning walk │    │
│  │ 5 days in a row. That's    │    │
│  │ fantastic! 🎉              │    │
│  │                        9:15 AM  │
│  └─────────────────────────────┘    │
│                                     │
│    ┌─────────────────────────────┐  │
│    │ Thanks! It's getting easier │  │
│    │ each day. I actually look   │  │
│    │ forward to it now 😊        │  │
│    │ 9:18 AM                     │  │
│    └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ That's the power of habit!  │    │
│  │ Your brain is rewiring      │    │
│  │ itself. Ready for the next  │    │
│  │ challenge?                  │    │
│  │                        9:19 AM  │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ What would you like to add? │    │
│  │ ┌─────────┐ ┌─────────┐     │    │
│  │ │Nutrition│ │ Sleep   │     │    │
│  │ └─────────┘ └─────────┘     │    │
│  │ ┌─────────┐                 │    │
│  │ │Mindset  │                 │    │
│  │ └─────────┘            9:19 AM  │
│  └─────────────────────────────┘    │
│                                     │
├─────────────────────────────────────┤
│ [Type your message...]        [🎤] │
└─────────────────────────────────────┘
```

### Message Types and Components

#### Text Messages
- **Standard text**: Regular conversation messages
- **Rich text**: Bold, italic, emoji support
- **Links**: Clickable links with preview
- **Mentions**: Highlight user name or achievements

#### Interactive Messages
```javascript
const InteractiveMessage = {
  type: "quick_replies",
  text: "How are you feeling about your progress today?",
  quick_replies: [
    { text: "Great! 😊", payload: "feeling_great" },
    { text: "Okay 😐", payload: "feeling_okay" },
    { text: "Struggling 😔", payload: "feeling_struggling" },
    { text: "Need help", payload: "need_help" }
  ]
};

const ProgressCheck = {
  type: "habit_check",
  text: "Time for your evening routine check-in!",
  habits: [
    { id: "meditation", name: "5-min meditation", completed: false },
    { id: "reading", name: "Read 10 pages", completed: true },
    { id: "journal", name: "Gratitude journal", completed: false }
  ],
  action_buttons: ["Mark Done", "Skip", "Reschedule"]
};
```

#### Media Messages
- **Images**: Progress photos, motivational images, infographics
- **Audio**: Voice messages from creator, guided meditations
- **Videos**: Short coaching clips, exercise demonstrations
- **Documents**: PDFs, worksheets, resources

### Typing Indicators and Status
```
┌─────────────────────────────────────┐
│  Sarah is typing... ●●●             │
└─────────────────────────────────────┘

Message Status Indicators:
✓ Sent
✓✓ Delivered  
✓✓ Read (blue checkmarks)
```

## Progress Tracking Interface

### Progress Dashboard
```
┌─────────────────────────────────────┐
│  ← Back        Progress             │
├─────────────────────────────────────┤
│           This Week                 │
│  ┌─────────────────────────────────┐ │
│  │     Habit Completion Rate       │ │
│  │                                 │ │
│  │         ████████░░ 85%          │ │
│  │                                 │ │
│  │    🔥 Current Streak: 12 days   │ │
│  │    🏆 Best Streak: 18 days      │ │
│  └─────────────────────────────────┘ │
│                                     │
│         Weekly Overview             │
│  ┌─────────────────────────────────┐ │
│  │ M  T  W  T  F  S  S             │ │
│  │ ✅ ✅ ✅ ❌ ✅ ✅ ⏳            │ │
│  │                                 │ │
│  │ Morning Walk: 6/7 days          │ │
│  │ Water Intake: 7/7 days          │ │
│  │ Meditation: 4/7 days            │ │
│  └─────────────────────────────────┘ │
│                                     │
│         Achievements                │
│  🏆 Early Bird (7 days)            │
│  🌟 Consistency Champion (14 days)  │
│  💧 Hydration Hero (30 days)       │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │        View Detailed Stats      │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Detailed Analytics
```
┌─────────────────────────────────────┐
│  ← Back    Detailed Analytics       │
├─────────────────────────────────────┤
│  📊 Last 30 Days                    │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │        Completion Trend         │ │
│  │   100% ┌─────────────────────┐  │ │
│  │    80% │     ╭─╮         ╭─╮ │  │ │
│  │    60% │   ╭─╯ │       ╭─╯ │ │  │ │
│  │    40% │ ╭─╯   │     ╭─╯   │ │  │ │
│  │    20% │╱      │   ╭─╯     │ │  │ │
│  │     0% └───────┴───┴───────┴─┘  │ │
│  │        Week 1 2 3 4             │ │
│  └─────────────────────────────────┘ │
│                                     │
│         Habit Breakdown             │
│  ┌─────────────────────────────────┐ │
│  │ 🏃‍♀️ Morning Walk                │ │
│  │ ████████████████░░░░ 80%        │ │
│  │ 24/30 days • 6 day streak       │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 💧 Water Intake                 │ │
│  │ ████████████████████ 100%       │ │
│  │ 30/30 days • 30 day streak      │ │
│  └─────────────────────────────────┘ │
│                                     │
│         Insights                    │
│  📈 Your consistency improved 15%   │
│  🎯 Best performance: Weekends      │
│  ⚠️  Challenge area: Wednesday      │
└─────────────────────────────────────┘
```

## Programs Interface

### Program Library
```
┌─────────────────────────────────────┐
│  ← Back        Programs             │
├─────────────────────────────────────┤
│         Active Programs             │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🏃‍♀️ 30-Day Fitness Foundation   │ │
│  │                                 │ │
│  │ Progress: ████████░░░░ 60%      │ │
│  │ Day 18 of 30                    │ │
│  │                                 │ │
│  │ Next: "Building Your Routine"   │ │
│  │ ┌─────────────┐ ┌─────────────┐ │ │
│  │ │  Continue   │ │   Details   │ │ │
│  │ └─────────────┘ └─────────────┘ │ │
│  └─────────────────────────────────┘ │
│                                     │
│       Available Programs            │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🧘‍♀️ Mindfulness Mastery         │ │
│  │                                 │ │
│  │ 21 days • Beginner friendly    │ │
│  │ Build daily meditation habit   │ │
│  │                                 │ │
│  │ ⭐⭐⭐⭐⭐ 4.9 (127 reviews)      │ │
│  │ ┌─────────────┐ ┌─────────────┐ │ │
│  │ │   Enroll    │ │   Preview   │ │ │
│  │ └─────────────┘ └─────────────┘ │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 💤 Sleep Optimization           │ │
│  │                                 │ │
│  │ 14 days • Intermediate          │ │
│  │ Improve sleep quality & energy │ │
│  │                                 │ │
│  │ ⭐⭐⭐⭐⭐ 4.8 (89 reviews)       │ │
│  │ ┌─────────────┐ ┌─────────────┐ │ │
│  │ │   Enroll    │ │   Preview   │ │ │
│  │ └─────────────┘ └─────────────┘ │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Program Detail View
```
┌─────────────────────────────────────┐
│  ← Back   30-Day Fitness Foundation │
├─────────────────────────────────────┤
│  [Program Hero Image]               │
│                                     │
│  Build sustainable fitness habits   │
│  that last a lifetime               │
│                                     │
│  📅 30 days  👥 1,247 enrolled      │
│  ⭐ 4.9 rating  🏆 89% completion   │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │          Your Progress          │ │
│  │                                 │ │
│  │  Day 18 of 30 ████████░░░░ 60% │ │
│  │                                 │ │
│  │  🔥 Current streak: 12 days     │ │
│  │  🏆 Badges earned: 3            │ │
│  │  📈 Consistency: 85%            │ │
│  └─────────────────────────────────┘ │
│                                     │
│         Program Outline             │
│                                     │
│  Week 1: Foundation Building        │
│  ✅ Day 1: Welcome & Goal Setting   │
│  ✅ Day 2: First Workout            │
│  ✅ Day 3: Habit Stacking           │
│  ...                               │
│                                     │
│  Week 3: Momentum Building (Current)│
│  ✅ Day 15: Strength Training       │
│  ✅ Day 16: Active Recovery         │
│  ✅ Day 17: Nutrition Focus         │
│  ➡️  Day 18: Building Your Routine  │
│  ⏳ Day 19: Cardio Challenge        │
│  ...                               │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │        Continue Program         │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Content Library

### Resource Organization
```
┌─────────────────────────────────────┐
│  ← Back        Library              │
├─────────────────────────────────────┤
│  🔍 [Search resources...]           │
│                                     │
│         Categories                  │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 📚 Articles & Guides            │ │
│  │ 12 resources                    │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🎥 Video Tutorials              │ │
│  │ 8 resources                     │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🎧 Audio Content                │ │
│  │ 15 resources                    │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 📋 Worksheets & Tools           │ │
│  │ 6 resources                     │ │
│  └─────────────────────────────────┘ │
│                                     │
│         Recently Added              │
│                                     │
│  📚 "The Science of Habit Formation"│
│  🎥 "5-Minute Morning Routine"      │
│  🎧 "Motivation vs. Discipline"     │
│                                     │
│         Bookmarked                  │
│                                     │
│  ⭐ "Goal Setting Worksheet"        │
│  ⭐ "Healthy Recipe Collection"     │
└─────────────────────────────────────┘
```

## Gamification Elements

### Achievement System
```javascript
const AchievementTypes = {
  streak_based: {
    "early_bird": {
      name: "Early Bird",
      description: "Complete morning routine 7 days in a row",
      icon: "🌅",
      tiers: [7, 14, 30, 90] // days
    },
    "consistency_champion": {
      name: "Consistency Champion", 
      description: "Maintain 80%+ completion rate",
      icon: "🏆",
      tiers: [7, 14, 30, 90] // days
    }
  },
  milestone_based: {
    "first_week": {
      name: "First Week Complete",
      description: "Completed your first week of coaching",
      icon: "🎉",
      one_time: true
    },
    "program_graduate": {
      name: "Program Graduate",
      description: "Successfully completed a full program",
      icon: "🎓",
      repeatable: true
    }
  },
  social_based: {
    "conversation_starter": {
      name: "Conversation Starter",
      description: "Sent 10 messages to your coach",
      icon: "💬",
      threshold: 10
    }
  }
};
```

### Progress Visualization
```javascript
const ProgressElements = {
  streak_counter: {
    display: "🔥 12 day streak",
    animation: "flame_flicker",
    milestone_celebrations: [7, 14, 30, 60, 90]
  },
  completion_rings: {
    daily: "circular_progress_ring",
    weekly: "segmented_ring",
    monthly: "calendar_heatmap"
  },
  level_system: {
    current_level: 3,
    progress_to_next: 0.65,
    level_names: ["Beginner", "Developing", "Consistent", "Advanced", "Master"]
  }
};
```

## Customization and Branding

### Creator Branding Elements
```javascript
const BrandingOptions = {
  colors: {
    primary: "#007bff", // Creator's brand color
    secondary: "#6c757d",
    accent: "#28a745",
    background: "#ffffff",
    text: "#212529"
  },
  typography: {
    heading_font: "Montserrat",
    body_font: "Open Sans",
    font_sizes: {
      small: 14,
      medium: 16,
      large: 18,
      xlarge: 24
    }
  },
  imagery: {
    logo: "creator_logo_url",
    avatar: "creator_avatar_url",
    background_pattern: "subtle_pattern_url",
    hero_images: ["image1_url", "image2_url"]
  },
  voice_and_tone: {
    greeting_style: "warm_and_encouraging",
    motivation_level: "high",
    formality: "casual_friendly",
    emoji_usage: "moderate"
  }
};
```

### Personalization Features
- **Custom welcome messages** from creator
- **Branded color schemes** throughout the app
- **Creator's photo/logo** in navigation and messages
- **Personalized content** based on user goals and preferences
- **Custom achievement badges** designed by creator

## Offline Functionality

### Offline Capabilities
- **Habit tracking**: Mark habits complete/incomplete
- **Progress viewing**: Access cached progress data
- **Content reading**: Previously downloaded articles and resources
- **Message drafting**: Compose messages for later sending
- **Basic navigation**: Access all main screens

### Sync Behavior
```javascript
const SyncStrategy = {
  immediate_sync: [
    "habit_completions",
    "message_sending",
    "achievement_unlocks"
  ],
  background_sync: [
    "progress_data",
    "content_downloads",
    "user_preferences"
  ],
  conflict_resolution: {
    habit_data: "merge_with_timestamp_priority",
    user_settings: "server_wins",
    messages: "append_all"
  }
};
```

## Accessibility Features

### Inclusive Design
- **VoiceOver/TalkBack support**: Full screen reader compatibility
- **Dynamic text sizing**: Respect system font size preferences
- **High contrast mode**: Alternative color schemes for visibility
- **Voice input**: Speech-to-text for message composition
- **Haptic feedback**: Tactile confirmation for important actions
- **Reduced motion**: Respect motion sensitivity preferences

### Accessibility Testing
- **Minimum touch targets**: 44x44 points for all interactive elements
- **Color contrast**: WCAG AA compliance (4.5:1 ratio minimum)
- **Focus indicators**: Clear visual focus for keyboard navigation
- **Alternative text**: Descriptive labels for all images and icons
- **Error messaging**: Clear, actionable error descriptions

## Performance Requirements

### Loading Performance
- **App launch**: < 3 seconds cold start
- **Screen transitions**: < 500ms between screens
- **Image loading**: Progressive loading with placeholders
- **Offline content**: Instant access to cached data

### Battery Optimization
- **Background processing**: Minimal battery usage when backgrounded
- **Network efficiency**: Batch API calls and cache responses
- **Animation optimization**: 60fps animations with efficient rendering
- **Location services**: Only when explicitly needed for features