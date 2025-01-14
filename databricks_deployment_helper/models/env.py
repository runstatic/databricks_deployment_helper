from enum import Enum


class Env(str, Enum):
    DEV = "DEV"
    PRE = "PRE"
    STG = "STG"
    PRD = "PRD"
