# Web Widget User Experience Specification

## Overview

The web widget provides a seamless, embeddable chat interface that integrates into creator websites, offering visitors immediate access to AI-powered coaching conversations. The widget is designed to be unobtrusive yet engaging, with customizable branding and responsive design.

## Design Principles

### Core UX Principles
1. **Non-Intrusive Integration**: Blends naturally with host website design
2. **Instant Accessibility**: One-click access to coaching conversations
3. **Progressive Engagement**: Gradually introduces advanced features
4. **Mobile-First Design**: Optimized for all device sizes
5. **Brand Consistency**: Reflects creator's visual identity
6. **Performance Optimized**: Minimal impact on host website performance

## Widget States and Behavior

### Collapsed State (Default)
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│                              ┌────┐ │
│                              │ 💬 │ │
│                              │    │ │
│                              └────┘ │
└─────────────────────────────────────┘
```

### Hover State
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│                        ┌──────────┐ │
│                        │ Chat with│ │
│                        │   Sarah  │ │
│                        │    💬    │ │
│                        └──────────┘ │
└─────────────────────────────────────┘
```

### Expanded State
```
┌─────────────────────────────────────┐
│                                     │
│              ┌────────────────────┐ │
│              │ Chat with Sarah  ✕ │ │
│              ├────────────────────┤ │
│              │                    │ │
│              │ Hi! I'm Sarah,     │ │
│              │ your wellness      │ │
│              │ coach. How can I   │ │
│              │ help you today?    │ │
│              │                    │ │
│              │ ┌────────────────┐ │ │
│              │ │ Get started    │ │ │
│              │ └────────────────┘ │ │
│              │ ┌────────────────┐ │ │
│              │ │ Learn more     │ │ │
│              │ └────────────────┘ │ │
│              │                    │ │
│              │ [Type message...]  │ │
│              └────────────────────┘ │
└─────────────────────────────────────┘
```## Wid
get Positioning and Layout

### Position Options
- **Bottom Right**: Default position, most common placement
- **Bottom Left**: Alternative for right-heavy layouts
- **Bottom Center**: For centered, prominent placement
- **Custom**: Absolute positioning with CSS coordinates

### Size Variations
```javascript
const WidgetSizes = {
  compact: {
    collapsed: { width: 60, height: 60 },
    expanded: { width: 320, height: 400 }
  },
  standard: {
    collapsed: { width: 70, height: 70 },
    expanded: { width: 380, height: 500 }
  },
  large: {
    collapsed: { width: 80, height: 80 },
    expanded: { width: 420, height: 600 }
  }
};
```

## Conversation Interface

### Chat Layout
```
┌────────────────────────────────────┐
│ Sarah Johnson              ✕ ─ □   │
│ 🟢 Online                          │
├────────────────────────────────────┤
│                                    │
│ ┌────────────────────────────────┐ │
│ │ Welcome! I'm here to help you  │ │
│ │ build healthier habits. What   │ │
│ │ would you like to work on?     │ │
│ │                           9:15 │ │
│ └────────────────────────────────┘ │
│                                    │
│   ┌──────────────────────────────┐ │
│   │ I want to start exercising   │ │
│   │ regularly but struggle with  │ │
│   │ motivation                   │ │
│   │ 9:18                         │ │
│   └──────────────────────────────┘ │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ That's a common challenge!     │ │
│ │ Let's start with small steps.  │ │
│ │ What type of exercise do you   │ │
│ │ enjoy most?                    │ │
│ │                           9:19 │ │
│ └────────────────────────────────┘ │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ Quick suggestions:             │ │
│ │ ┌──────────┐ ┌──────────┐     │ │
│ │ │ Walking  │ │ Swimming │     │ │
│ │ └──────────┘ └──────────┘     │ │
│ │ ┌──────────┐ ┌──────────┐     │ │
│ │ │ Yoga     │ │ Dancing  │     │ │
│ │ └──────────┘ └──────────┘     │ │
│ │                           9:19 │ │
│ └────────────────────────────────┘ │
│                                    │
├────────────────────────────────────┤
│ [Type your message...]       [🎤] │
└────────────────────────────────────┘
```

### Message Types

#### Text Messages
- **Standard text**: Regular conversation messages
- **Rich formatting**: Bold, italic, links
- **Emoji support**: Full emoji keyboard integration
- **Auto-linking**: URLs automatically become clickable

#### Interactive Elements
```javascript
const QuickReplies = {
  type: "quick_replies",
  options: [
    { text: "Tell me more", action: "expand_topic" },
    { text: "Get started", action: "begin_program" },
    { text: "Not interested", action: "change_topic" }
  ],
  max_visible: 3,
  style: "button" // or "chip"
};

const SuggestedActions = {
  type: "suggested_actions",
  actions: [
    { 
      text: "Schedule a call",
      icon: "📞",
      action: "open_calendar"
    },
    {
      text: "Download guide", 
      icon: "📚",
      action: "download_resource"
    }
  ]
};
```

## Customization Options

### Visual Branding
```javascript
const BrandingConfig = {
  colors: {
    primary: "#007bff",
    secondary: "#6c757d", 
    background: "#ffffff",
    text: "#212529",
    accent: "#28a745"
  },
  typography: {
    font_family: "Inter, sans-serif",
    font_sizes: {
      small: "12px",
      medium: "14px", 
      large: "16px"
    }
  },
  avatar: {
    creator_photo: "https://example.com/avatar.jpg",
    fallback_initials: "SJ",
    shape: "circle" // or "square", "rounded"
  },
  widget_style: {
    border_radius: "12px",
    shadow: "0 4px 12px rgba(0,0,0,0.15)",
    animation: "slide_up" // or "fade_in", "scale"
  }
};
```

### Behavioral Configuration
```javascript
const BehaviorConfig = {
  auto_open: {
    enabled: false,
    delay_seconds: 5,
    conditions: ["first_visit", "return_visitor"]
  },
  proactive_messages: {
    enabled: true,
    triggers: [
      {
        condition: "time_on_page",
        threshold: 30, // seconds
        message: "Hi! I noticed you're browsing our wellness content. Any questions I can help with?"
      },
      {
        condition: "scroll_percentage", 
        threshold: 75,
        message: "Interested in starting your wellness journey? I'm here to help!"
      }
    ]
  },
  offline_behavior: {
    show_offline_message: true,
    collect_contact_info: true,
    offline_message: "I'm currently offline, but I'd love to help! Leave your email and I'll get back to you soon."
  }
};
```

## Responsive Design

### Mobile Optimization
```css
/* Mobile-first responsive design */
@media (max-width: 768px) {
  .widget-expanded {
    width: 100vw;
    height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    border-radius: 0;
  }
  
  .widget-header {
    padding: 16px;
    font-size: 18px;
  }
  
  .message-input {
    font-size: 16px; /* Prevent zoom on iOS */
    padding: 12px;
  }
}

@media (max-width: 480px) {
  .quick-reply-button {
    font-size: 14px;
    padding: 8px 12px;
    margin: 4px;
  }
}
```

### Tablet Adaptation
- **Medium size**: Balanced between mobile and desktop
- **Touch-friendly**: Larger touch targets for buttons
- **Landscape mode**: Optimized for horizontal orientation

## Integration Methods

### JavaScript Embed
```html
<!-- Simple embed code -->
<script>
  (function(w,d,s,o,f,js,fjs){
    w['CoachingWidget']=o;w[o]=w[o]||function(){
    (w[o].q=w[o].q||[]).push(arguments)};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }(window,document,'script','cw','https://widget.coaching-platform.com/widget.js'));
  
  cw('init', {
    creator_id: 'your-creator-id',
    position: 'bottom-right',
    theme: 'auto'
  });
</script>
```

### WordPress Plugin
```php
// WordPress shortcode integration
[coaching_widget creator_id="your-creator-id" position="bottom-right"]

// PHP function for theme integration
<?php echo do_shortcode('[coaching_widget creator_id="your-creator-id"]'); ?>
```

### React Component
```jsx
import { CoachingWidget } from '@coaching-platform/react-widget';

function App() {
  return (
    <div>
      {/* Your app content */}
      <CoachingWidget
        creatorId="your-creator-id"
        position="bottom-right"
        theme={{
          primaryColor: "#007bff",
          fontFamily: "Inter"
        }}
        onMessage={(message) => console.log('New message:', message)}
      />
    </div>
  );
}
```

## Performance Optimization

### Loading Strategy
```javascript
const LoadingStrategy = {
  lazy_loading: {
    initial_load: ["widget_button", "basic_styles"],
    on_interaction: ["chat_interface", "conversation_history"],
    on_demand: ["file_upload", "voice_messages"]
  },
  caching: {
    static_assets: "1 year",
    conversation_data: "24 hours", 
    user_preferences: "7 days"
  },
  compression: {
    javascript: "gzip + minification",
    css: "minification + critical_css_inline",
    images: "webp_with_fallback"
  }
};
```

### Bundle Size Optimization
- **Core widget**: < 50KB gzipped
- **Full features**: < 150KB gzipped
- **Progressive loading**: Features load as needed
- **Tree shaking**: Unused features excluded

## Analytics and Tracking

### Built-in Analytics
```javascript
const AnalyticsEvents = {
  widget_events: [
    "widget_loaded",
    "widget_opened", 
    "widget_closed",
    "message_sent",
    "message_received"
  ],
  engagement_metrics: [
    "session_duration",
    "messages_per_session",
    "return_visitor",
    "conversion_events"
  ],
  performance_metrics: [
    "load_time",
    "response_time",
    "error_rate"
  ]
};
```

### Custom Event Tracking
```javascript
// Track custom events
cw('track', 'custom_event', {
  event_name: 'program_signup',
  program_id: 'fitness-basics',
  user_id: 'anonymous_user_123'
});

// Integration with Google Analytics
cw('config', {
  analytics: {
    google_analytics: 'GA-MEASUREMENT-ID',
    facebook_pixel: 'FB-PIXEL-ID'
  }
});
```

## Accessibility Features

### WCAG 2.1 AA Compliance
- **Keyboard navigation**: Full keyboard accessibility
- **Screen reader support**: Proper ARIA labels and roles
- **Color contrast**: Minimum 4.5:1 ratio
- **Focus management**: Clear focus indicators
- **Alternative text**: Descriptive text for images and icons

### Accessibility Configuration
```javascript
const AccessibilityConfig = {
  high_contrast: {
    enabled: false,
    auto_detect: true // Detect system preference
  },
  reduced_motion: {
    respect_preference: true,
    fallback_animations: "fade_only"
  },
  font_scaling: {
    respect_system_size: true,
    max_scale: 1.5
  },
  keyboard_navigation: {
    enabled: true,
    focus_trap: true, // Keep focus within widget when open
    escape_to_close: true
  }
};
```

## Security Considerations

### Data Protection
- **HTTPS only**: All communications encrypted
- **CSP headers**: Content Security Policy implementation
- **XSS prevention**: Input sanitization and output encoding
- **CSRF protection**: Token-based request validation

### Privacy Features
```javascript
const PrivacyConfig = {
  data_collection: {
    minimal_data: true,
    explicit_consent: true,
    retention_period: "2_years"
  },
  cookies: {
    essential_only: true,
    consent_banner: true,
    gdpr_compliant: true
  },
  user_control: {
    data_export: true,
    data_deletion: true,
    conversation_history_control: true
  }
};
```

## Testing and Quality Assurance

### Cross-Browser Testing
- **Modern browsers**: Chrome, Firefox, Safari, Edge
- **Mobile browsers**: iOS Safari, Chrome Mobile, Samsung Internet
- **Legacy support**: IE11 graceful degradation

### Performance Testing
- **Load testing**: Widget performance under high traffic
- **Memory usage**: Prevent memory leaks in long sessions
- **Network conditions**: Optimization for slow connections
- **Battery impact**: Minimal battery drain on mobile devices

### User Testing Scenarios
1. **First-time visitor**: Initial interaction and onboarding
2. **Return visitor**: Conversation continuity and recognition
3. **Mobile user**: Touch interactions and responsive behavior
4. **Accessibility user**: Screen reader and keyboard navigation
5. **Slow connection**: Performance on limited bandwidth