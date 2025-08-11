# Program Builder Logic Specification

## Overview

The Program Builder is a visual, drag-and-drop interface that enables creators to design complex coaching workflows without coding. It combines the simplicity of flowchart creation with the power of conditional logic, timing controls, and dynamic user interactions.

## Core Architecture

### Node-Based System
The program builder uses a node-based architecture where each node represents a specific action or decision point in the coaching journey.

```javascript
const NodeTypes = {
  START: "program_entry_point",
  MESSAGE: "send_message_to_user", 
  QUESTION: "ask_user_question",
  WAIT: "pause_execution",
  CONDITION: "conditional_branching",
  ACTION: "perform_system_action",
  REWARD: "grant_badge_or_reward",
  END: "program_completion"
};
```

### Flow Execution Engine

#### State Management
```javascript
class ProgramExecutionState {
  constructor(programId, userId) {
    this.programId = programId;
    this.userId = userId;
    this.currentNode = null;
    this.variables = new Map();
    this.executionHistory = [];
    this.pausedUntil = null;
    this.status = 'active'; // active, paused, completed, failed
  }

  async executeNextNode() {
    if (this.isPaused()) {
      return { status: 'paused', resumeAt: this.pausedUntil };
    }

    const node = await this.getCurrentNode();
    const result = await this.executeNode(node);
    
    this.recordExecution(node, result);
    this.updateCurrentNode(result.nextNode);
    
    return result;
  }

  isPaused() {
    return this.pausedUntil && new Date() < this.pausedUntil;
  }
}
```

#### Node Execution Logic
```javascript
class NodeExecutor {
  async executeNode(node, executionState) {
    switch (node.type) {
      case 'START':
        return this.executeStartNode(node, executionState);
      case 'MESSAGE':
        return this.executeMessageNode(node, executionState);
      case 'QUESTION':
        return this.executeQuestionNode(node, executionState);
      case 'WAIT':
        return this.executeWaitNode(node, executionState);
      case 'CONDITION':
        return this.executeConditionNode(node, executionState);
      case 'REWARD':
        return this.executeRewardNode(node, executionState);
      case 'END':
        return this.executeEndNode(node, executionState);
      default:
        throw new Error(`Unknown node type: ${node.type}`);
    }
  }
}
```

## Node Types and Specifications

### Start Node
```javascript
const StartNodeConfig = {
  type: "START",
  id: "start_node",
  properties: {
    program_name: "string",
    description: "string",
    enrollment_requirements: {
      prerequisites: ["array_of_program_ids"],
      user_attributes: {
        min_engagement_score: "number",
        required_goals: ["array_of_goal_types"]
      }
    }
  },
  outputs: {
    success: "next_node_id",
    requirements_not_met: "alternative_node_id"
  }
};
```

### Message Node
```javascript
const MessageNodeConfig = {
  type: "MESSAGE",
  id: "message_node_1",
  properties: {
    message_content: {
      text: "string_with_variables",
      media_url: "optional_string",
      media_type: "image|video|audio|document",
      formatting: "markdown|html|plain"
    },
    personalization: {
      use_user_name: "boolean",
      use_user_goals: "boolean",
      use_progress_data: "boolean",
      custom_variables: ["array_of_variable_names"]
    },
    delivery_options: {
      immediate: "boolean",
      delay_minutes: "number",
      optimal_timing: "boolean", // AI-determined best time
      retry_if_unread: {
        enabled: "boolean",
        max_retries: "number",
        retry_interval_hours: "number"
      }
    },
    interaction_options: {
      quick_replies: ["array_of_reply_options"],
      expected_response_type: "text|choice|media|none",
      response_timeout_hours: "number"
    }
  },
  outputs: {
    sent: "next_node_id",
    failed: "error_handler_node_id",
    user_responded: "response_handler_node_id",
    timeout: "timeout_handler_node_id"
  }
};
```

### Question Node
```javascript
const QuestionNodeConfig = {
  type: "QUESTION",
  id: "question_node_1", 
  properties: {
    question: {
      text: "string_with_variables",
      question_type: "open_ended|multiple_choice|scale|yes_no",
      required: "boolean"
    },
    multiple_choice_options: {
      options: [
        { value: "option_1", label: "Display Text 1" },
        { value: "option_2", label: "Display Text 2" }
      ],
      allow_multiple: "boolean",
      randomize_order: "boolean"
    },
    scale_options: {
      min_value: "number",
      max_value: "number", 
      step: "number",
      min_label: "string",
      max_label: "string"
    },
    validation: {
      min_length: "number",
      max_length: "number",
      pattern: "regex_string",
      custom_validation: "function_reference"
    },
    follow_up: {
      clarification_prompts: ["array_of_follow_up_questions"],
      max_clarifications: "number"
    }
  },
  outputs: {
    answered: "next_node_id",
    skipped: "skip_handler_node_id",
    invalid_response: "validation_error_node_id",
    // Dynamic outputs based on answer
    conditional_outputs: [
      {
        condition: "answer_equals_value",
        value: "specific_answer",
        next_node: "conditional_node_id"
      }
    ]
  }
};
```

### Wait Node
```javascript
const WaitNodeConfig = {
  type: "WAIT",
  id: "wait_node_1",
  properties: {
    wait_type: "fixed_duration|until_time|until_condition|user_action",
    duration: {
      amount: "number",
      unit: "minutes|hours|days|weeks"
    },
    until_time: {
      time: "HH:MM",
      timezone: "user_timezone|specific_timezone",
      next_occurrence: "boolean" // wait until next occurrence of time
    },
    until_condition: {
      condition_type: "user_activity|external_event|date_reached",
      condition_details: "object_specific_to_condition_type"
    },
    user_action: {
      action_type: "message_sent|habit_completed|goal_updated",
      timeout_hours: "number" // max time to wait
    },
    during_wait: {
      allow_user_interaction: "boolean",
      reminder_messages: [
        {
          delay_hours: "number",
          message: "string"
        }
      ]
    }
  },
  outputs: {
    wait_completed: "next_node_id",
    timeout: "timeout_node_id",
    interrupted: "interruption_handler_node_id"
  }
};
```

### Condition Node
```javascript
const ConditionNodeConfig = {
  type: "CONDITION",
  id: "condition_node_1",
  properties: {
    conditions: [
      {
        variable: "user_attribute|program_variable|system_value",
        operator: "equals|not_equals|greater_than|less_than|contains|in_range",
        value: "comparison_value",
        data_type: "string|number|boolean|date|array"
      }
    ],
    logic_operator: "AND|OR", // for multiple conditions
    evaluation_context: {
      use_current_data: "boolean",
      cache_duration_minutes: "number"
    }
  },
  outputs: {
    condition_true: "true_path_node_id",
    condition_false: "false_path_node_id",
    evaluation_error: "error_handler_node_id"
  }
};
```

### Action Node
```javascript
const ActionNodeConfig = {
  type: "ACTION",
  id: "action_node_1",
  properties: {
    action_type: "update_user_profile|send_notification|create_task|log_event|call_webhook",
    action_details: {
      // Specific to action type
      update_user_profile: {
        attributes: {
          "attribute_name": "new_value"
        }
      },
      send_notification: {
        title: "string",
        body: "string", 
        type: "push|email|sms",
        schedule: "immediate|delayed"
      },
      create_task: {
        title: "string",
        description: "string",
        due_date: "date_string",
        priority: "low|medium|high"
      },
      call_webhook: {
        url: "webhook_url",
        method: "GET|POST|PUT",
        headers: "object",
        payload: "object"
      }
    },
    error_handling: {
      retry_attempts: "number",
      retry_delay_seconds: "number",
      continue_on_error: "boolean"
    }
  },
  outputs: {
    success: "next_node_id",
    failed: "error_handler_node_id"
  }
};
```

### Reward Node
```javascript
const RewardNodeConfig = {
  type: "REWARD",
  id: "reward_node_1",
  properties: {
    reward_type: "badge|points|unlock_content|custom_reward",
    badge_details: {
      badge_id: "string",
      custom_message: "string",
      celebration_animation: "boolean"
    },
    points_details: {
      points_amount: "number",
      points_category: "string",
      bonus_multiplier: "number"
    },
    unlock_content: {
      content_type: "program|resource|feature",
      content_id: "string",
      access_duration: "permanent|temporary",
      expiry_days: "number"
    },
    notification: {
      send_notification: "boolean",
      notification_message: "string",
      celebration_level: "subtle|moderate|enthusiastic"
    }
  },
  outputs: {
    reward_granted: "next_node_id",
    reward_failed: "error_handler_node_id",
    already_earned: "duplicate_handler_node_id"
  }
};
```

### End Node
```javascript
const EndNodeConfig = {
  type: "END",
  id: "end_node",
  properties: {
    completion_type: "success|failure|user_exit|timeout",
    completion_message: "string",
    final_actions: {
      update_user_status: "boolean",
      send_completion_certificate: "boolean",
      unlock_next_program: "program_id",
      schedule_follow_up: {
        enabled: "boolean",
        delay_days: "number",
        follow_up_program: "program_id"
      }
    },
    analytics: {
      track_completion: "boolean",
      completion_metrics: ["array_of_metric_names"],
      custom_events: ["array_of_event_objects"]
    }
  },
  outputs: {} // End nodes have no outputs
};
```

## Flow Control Logic

### Conditional Branching
```javascript
class ConditionalLogic {
  evaluateCondition(condition, userContext) {
    const { variable, operator, value, dataType } = condition;
    const actualValue = this.getVariableValue(variable, userContext);
    
    return this.compareValues(actualValue, operator, value, dataType);
  }

  compareValues(actual, operator, expected, dataType) {
    // Type conversion based on dataType
    const convertedActual = this.convertValue(actual, dataType);
    const convertedExpected = this.convertValue(expected, dataType);

    switch (operator) {
      case 'equals':
        return convertedActual === convertedExpected;
      case 'not_equals':
        return convertedActual !== convertedExpected;
      case 'greater_than':
        return convertedActual > convertedExpected;
      case 'less_than':
        return convertedActual < convertedExpected;
      case 'contains':
        return convertedActual.includes(convertedExpected);
      case 'in_range':
        const [min, max] = convertedExpected;
        return convertedActual >= min && convertedActual <= max;
      default:
        throw new Error(`Unknown operator: ${operator}`);
    }
  }
}
```

### Variable Management
```javascript
class VariableManager {
  constructor() {
    this.systemVariables = new Map();
    this.userVariables = new Map();
    this.programVariables = new Map();
  }

  setVariable(scope, name, value) {
    const scopeMap = this.getScopeMap(scope);
    scopeMap.set(name, {
      value: value,
      timestamp: new Date(),
      type: typeof value
    });
  }

  getVariable(scope, name, defaultValue = null) {
    const scopeMap = this.getScopeMap(scope);
    const variable = scopeMap.get(name);
    return variable ? variable.value : defaultValue;
  }

  // Built-in system variables
  getSystemVariables(userContext) {
    return {
      current_time: new Date(),
      user_timezone: userContext.timezone,
      user_name: userContext.profile.name,
      user_goals: userContext.profile.goals,
      engagement_score: userContext.metrics.engagementScore,
      days_since_start: this.calculateDaysSinceStart(userContext),
      completion_percentage: this.calculateCompletionPercentage(userContext)
    };
  }
}
```

## Timing and Scheduling

### Execution Timing
```javascript
class TimingController {
  async scheduleNodeExecution(nodeId, executionTime, userContext) {
    const job = {
      id: this.generateJobId(),
      nodeId: nodeId,
      userId: userContext.userId,
      programId: userContext.programId,
      scheduledFor: executionTime,
      status: 'scheduled'
    };

    await this.scheduleJob(job);
    return job.id;
  }

  calculateOptimalTiming(userContext, nodeConfig) {
    const userPreferences = userContext.preferences;
    const historicalData = userContext.activityPatterns;
    
    // AI-driven optimal timing calculation
    const optimalTime = this.aiTimingPredictor.predict({
      userTimezone: userContext.timezone,
      preferredTimes: userPreferences.communicationTimes,
      responsePatterns: historicalData.responseRates,
      contentType: nodeConfig.type,
      urgency: nodeConfig.urgency || 'normal'
    });

    return optimalTime;
  }

  handleTimezoneDifferences(scheduledTime, userTimezone) {
    return moment(scheduledTime)
      .tz(userTimezone)
      .format();
  }
}
```

### Wait Logic Implementation
```javascript
class WaitLogic {
  async executeWait(waitNode, executionState) {
    const waitConfig = waitNode.properties;
    
    switch (waitConfig.wait_type) {
      case 'fixed_duration':
        return this.waitFixedDuration(waitConfig.duration, executionState);
      
      case 'until_time':
        return this.waitUntilTime(waitConfig.until_time, executionState);
      
      case 'until_condition':
        return this.waitUntilCondition(waitConfig.until_condition, executionState);
      
      case 'user_action':
        return this.waitForUserAction(waitConfig.user_action, executionState);
    }
  }

  async waitFixedDuration(duration, executionState) {
    const resumeTime = moment()
      .add(duration.amount, duration.unit)
      .toDate();
    
    executionState.pausedUntil = resumeTime;
    
    // Schedule reminder messages if configured
    if (waitConfig.during_wait?.reminder_messages) {
      this.scheduleReminders(waitConfig.during_wait.reminder_messages, executionState);
    }

    return {
      status: 'waiting',
      resumeAt: resumeTime,
      nextNode: waitNode.outputs.wait_completed
    };
  }
}
```

## Error Handling and Recovery

### Error Types and Handling
```javascript
class ErrorHandler {
  handleNodeExecutionError(error, node, executionState) {
    const errorType = this.classifyError(error);
    
    switch (errorType) {
      case 'NETWORK_ERROR':
        return this.handleNetworkError(error, node, executionState);
      
      case 'VALIDATION_ERROR':
        return this.handleValidationError(error, node, executionState);
      
      case 'USER_INPUT_ERROR':
        return this.handleUserInputError(error, node, executionState);
      
      case 'SYSTEM_ERROR':
        return this.handleSystemError(error, node, executionState);
      
      default:
        return this.handleUnknownError(error, node, executionState);
    }
  }

  async handleNetworkError(error, node, executionState) {
    const retryConfig = node.properties.error_handling;
    
    if (executionState.retryCount < retryConfig.retry_attempts) {
      executionState.retryCount++;
      
      // Exponential backoff
      const delay = Math.pow(2, executionState.retryCount) * retryConfig.retry_delay_seconds;
      
      setTimeout(() => {
        this.retryNodeExecution(node, executionState);
      }, delay * 1000);
      
      return { status: 'retrying', delay: delay };
    } else {
      return this.escalateToErrorNode(node, executionState, error);
    }
  }
}
```

## Testing and Validation

### Program Flow Testing
```javascript
class ProgramTester {
  async testProgramFlow(programDefinition, testScenarios) {
    const results = [];
    
    for (const scenario of testScenarios) {
      const testResult = await this.runTestScenario(programDefinition, scenario);
      results.push(testResult);
    }
    
    return this.generateTestReport(results);
  }

  async runTestScenario(programDefinition, scenario) {
    const mockExecutionState = this.createMockExecutionState(scenario.userContext);
    const simulator = new ProgramSimulator(programDefinition);
    
    try {
      const executionPath = await simulator.simulate(mockExecutionState, scenario.inputs);
      
      return {
        scenario: scenario.name,
        status: 'passed',
        executionPath: executionPath,
        finalState: mockExecutionState,
        assertions: this.validateAssertions(scenario.expectedOutcomes, executionPath)
      };
    } catch (error) {
      return {
        scenario: scenario.name,
        status: 'failed',
        error: error.message,
        executionPath: mockExecutionState.executionHistory
      };
    }
  }
}
```

This comprehensive program builder logic provides the foundation for creating sophisticated, interactive coaching programs that can adapt to user behavior, handle complex timing requirements, and provide robust error handling and recovery mechanisms.