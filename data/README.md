# Historical reservation dataset

## Source

Dataset: University Library Room Reservations
Publisher: Aceeedev
Source: https://www.kaggle.com/datasets/aceeedev/university-library-room-reservations

The dataset contains historical reservations from 2024.
It is used for descriptive reservation-demand analytics and is
separate from Roomly's live booking data.

## Licence and permitted use

The dataset licence and applicable attribution requirements must
be verified against the source page before submission.

This document does not claim a verified licence or permission
to redistribute the dataset.

## Files

| File | Description |
|---|---|
| reservations.csv | Raw dataset containing 51,826 records |
| reservations_cleaned_newversion.csv | Cleaned dataset containing 51,319 records |
| DATA_DICTIONARY.md | Field definitions and interpretation |

## Preparation

The documented cleaning excluded:

- One reservation with duration below five minutes.
- 506 reservations with duration above 240 minutes.

The cleaned dataset retains 51,319 records and 46 room identifiers.
These duration thresholds are analysis rules, not live booking rules.

Room identifiers must be loaded as text to preserve leading zeros.
Reservation duration is calculated from start and end timestamps.

The source timezone is unknown. Timestamps are treated as
timezone-naive source-local times without conversion.

## Reproduction

Follow [the analytics instructions](../analytics/README.md) to
analyse the supplied cleaned dataset and regenerate the outputs.

A standalone raw-to-cleaned preparation script is not included.
The submission therefore reproduces analysis of the cleaned data,
rather than the complete cleaning workflow.

## Limitations and responsible use

The dataset does not establish attendance or physical occupancy.
It does not contain live Roomly user identities or participant lists.

Two overlapping reservation cases were retained and documented.
Nine dates had no reservation starts; the source does not establish
whether these represent closures, zero demand or missing data.

Historical room identifiers remain separate from fictional
Roomly demonstration rooms. Results describe historical demand,
not no-show predictions or forecasts.

## Supporting documentation

- [Data dictionary](DATA_DICTIONARY.md)
- [Analytics method](../analytics/README.md)
- [Validation evidence](../evidence/test-data-ai.md)
