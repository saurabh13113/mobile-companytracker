import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call


# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancellation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class TermContract(Contract):
    """ The term contract for a phone line

    A term contract is a type of Contract with a specific start date and end
    date,and which requires a commitment until the end date. A term contract
    comes with an initial large term deposit added to the bill of the
    first month of the contract. This term deposit is a special amount that will
    be returned to the customer if and only if the customer cancels the contract
    after specified return date.

    === Public Attributes ===
    end:
        ending date for the contract

    === Private Attributes ===
    current:
        list storing values of month and year of contract

    """
    end: datetime.date
    _current: [datetime.date.month, datetime.date.year]

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """ Create a new Contract with the <start> date, and <end> date,
        starts as inactive"""
        Contract.__init__(self, start)
        self.end = end
        self._current = [start.month, start.year]

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        self.bill = bill
        self.bill.add_fixed_cost(TERM_MONTHLY_FEE)
        self.bill.set_rates("TERM", TERM_MINS_COST)
        if month == self.start.month and year == self.start.year:
            self.bill.add_fixed_cost(TERM_DEPOSIT)
        self._current = [month, year]

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill. First all free minutes are used and only
        from then onwards do call minutes start getting billed.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_free_minutes(ceil((call.duration / 60)))
        if self.bill.free_min > TERM_MINS:
            self.bill.add_billed_minutes(self.bill.free_min - TERM_MINS)
            self.bill.free_min = TERM_MINS

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract. If date of cancellation is after specified end date
        term deposit is returned to customer by deducting amount from bill.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancellation is requested.
        """
        self.start = None
        self.end = None
        if self.end.month < self._current[0] and self.end.year == \
                self._current[1]:
            self.bill.fixed_cost -= TERM_DEPOSIT
        elif self.end.year < self._current[1]:
            self.bill.fixed_cost -= TERM_DEPOSIT
        return self.bill.get_cost()


class MTMContract(Contract):
    """ The Month-to-Month contract for a phone line.

    The month-to-month contract is a Contract with no end date and no initial
    term deposit. This type of contract has higher rates for calls than a term
    contract, and comes with no free minutes included, but also involves no
    term commitment.

    """

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        self.bill = bill
        self.bill.set_rates("MTM", MTM_MINS_COST)
        self.bill.add_fixed_cost(MTM_MONTHLY_FEE)


class PrepaidContract(Contract):
    """ The Prepaid contract for a phone line

    A prepaid contract has a start date but does not have an end date,
    and it comes with no included minutes.It has an associated balance,
    which is the amount of money the customer owes. If the balance is negative,
    this indicates that the customer has this much credit, that is, has prepaid
    this much. The customer must prepay some amount when signing up for the
    prepaid contract, but it can be any amount.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    === Private Attributes ===
    balance:
        the current balance of the phone line for the customer.
    """
    _balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:
        """ Create a new Contract with the <start> date and set an initial
        balance with <balance>,contract starts as inactive.
        """
        Contract.__init__(self, start)
        self._balance = -balance

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        If the balance available ever becomes less than 10 then
        customer will have to load up at least 25 dollars in credit.
        """
        self.bill = bill
        self.bill.set_rates("PREPAID", PREPAID_MINS_COST)
        if self._balance > -10:
            if month == self.start.month and year == self.start.year:
                self.bill.add_fixed_cost(self._balance)
            else:
                self._balance -= 25
                self.bill.add_fixed_cost(25 + self._balance)
        else:
            self.bill.add_fixed_cost(self._balance)

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill. First all free minutes are used and only
        from then onwards do call minutes start getting billed.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        Contract.bill_call(self, call)
        self._balance += ceil(call.duration / 60) * PREPAID_MINS_COST

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract. If balance is negative that amount is forfeited and
        not given back. Else the balance is returned to customer.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancellation is requested.
        """
        self.start = None
        if self._balance < 0:
            return 0.00
        else:
            return self.bill.get_cost()


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
