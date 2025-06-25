/**
 * @name Financial Security Checks for DiceBot
 * @description Custom security queries for financial/gambling applications
 * @kind problem
 * @problem.severity warning
 * @security-severity 8.0
 * @precision high
 * @id py/dicebot-financial-security
 * @tags security
 *       financial
 *       gambling
 *       external/cwe/cwe-662
 */

import python

// Check for hardcoded financial values
class HardcodedFinancialValue extends StrConst {
  HardcodedFinancialValue() {
    // Look for potential hardcoded amounts, keys, or sensitive values
    this.getText().regexpMatch(".*([0-9]+\\.[0-9]{8,}|[a-fA-F0-9]{32,}|secret|key|token).*") and
    not this.getLocation().getFile().getAbsolutePath().matches("%test%")
  }
}

// Check for decimal precision issues in financial calculations
class UnsafeFloatCalculation extends BinaryExpr {
  UnsafeFloatCalculation() {
    this.getOp() instanceof Mult or this.getOp() instanceof Div and
    exists(Attribute attr | 
      attr.getName() = "bet" or 
      attr.getName() = "balance" or 
      attr.getName() = "capital" or
      attr.getName() = "amount"
    ) and
    not this.getLocation().getFile().getAbsolutePath().matches("%test%")
  }
}

// Check for random number generation in financial context
class UnsafeRandomUsage extends CallExpr {
  UnsafeRandomUsage() {
    exists(Attribute attr |
      attr.getName() = "random" or attr.getName() = "randint" or attr.getName() = "choice"
    ) and
    this.getFunc() = attr and
    not this.getLocation().getFile().getAbsolutePath().matches("%test%")
  }
}

from Expr e, string message
where
  (
    e instanceof HardcodedFinancialValue and
    message = "Potential hardcoded financial value or secret detected"
  ) or (
    e instanceof UnsafeFloatCalculation and
    message = "Float arithmetic used in financial calculation - consider using Decimal"
  ) or (
    e instanceof UnsafeRandomUsage and
    message = "Standard random functions used - ensure cryptographic security for gambling"
  )
select e, message
