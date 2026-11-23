from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Candidate(BaseModel):
    """A short option considered for the weekly learning pick."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Short, specific name for this week's learning work.")
    rationale: str = Field(description="Why this is a useful next step for this learner, based on the supplied profile and weekly digests.")


class SelectedPick(BaseModel):
    """Detailed one-week plan for the selected candidate only."""

    model_config = ConfigDict(extra="forbid")

    outcome: str = Field(description="The selected pick's useful result and observable conditions that mean the work is complete, scoped to one week.")
    first_step: str = Field(description="The first concrete action the learner can take to begin the selected pick.")
    core_ideas: list[str] = Field(
        min_length=3, max_length=5,
        description="Three to five focused questions the learner should be able to answer in their own words after completing the selected pick.",
    )


class ProfileAddition(BaseModel):
    """A proposed, evidence-backed edit to the learner's knowledge profile."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["add_item", "merge_items", "rename_item", "create_section"] = Field(
        description="Profile operation: add_item for a new concept, merge_items to consolidate related existing concepts, rename_item to refine one existing concept, or create_section to add a new profile category and its first item.",
    )
    section_id: str | None = Field(
        default=None,
        description="Identifier of an existing profile section for add_item, merge_items, and rename_item. Leave null for create_section.",
    )
    new_section_name: str | None = Field(
        default=None,
        description="Name for the new section when type is create_section. Do not supply this for other operations.",
    )
    target_item_ids: list[str] = Field(
        default_factory=list,
        description="Existing item identifiers to rename or merge. Use exactly one for rename_item, two or more from the same section for merge_items, and an empty list for add_item or create_section.",
    )
    item_name: str = Field(description="Clear topic label for the new or consolidated profile item; it must not claim proficiency or mastery.")
    source_pick_ids: list[str] = Field(
        min_length=1,
        description="Identifiers of completed picks in the supplied pending evidence that support this profile change. Only reference identifiers provided in the context.",
    )
    reasoning: str = Field(description="Why this topic label should be added, consolidated, or renamed based on completed pick titles. Do not claim skill or mastery.")

    @model_validator(mode="after")
    def validate_operation_shape(self):
        if self.type == "create_section":
            if not self.new_section_name or self.section_id or self.target_item_ids:
                raise ValueError("create_section requires new_section_name and no section_id or target_item_ids")
        elif not self.section_id or self.new_section_name:
            raise ValueError("item operations require section_id and must not include new_section_name")
        if self.type == "rename_item" and len(self.target_item_ids) != 1:
            raise ValueError("rename_item requires exactly one target item")
        if self.type == "merge_items" and len(self.target_item_ids) < 2:
            raise ValueError("merge_items requires at least two target items")
        if self.type == "add_item" and self.target_item_ids:
            raise ValueError("add_item must not include target_item_ids")
        return self


class PickProposal(BaseModel):
    """The complete weekly picker response."""

    model_config = ConfigDict(extra="forbid")

    candidates: list[Candidate] = Field(
        min_length=3, max_length=3,
        description="Exactly three meaningfully different week-sized learning options.",
    )
    selected_index: int = Field(
        ge=0, le=2,
        description="Zero-based index of the candidate that best fits the selection criteria.",
    )
    selected_pick: SelectedPick = Field(
        description="Detailed plan fields for the selected candidate only; do not generate these details for the other candidates.",
    )
    selection_reason: str = Field(description="Why the selected candidate is the best fit compared with the other two options.")
    profile_additions: list[ProfileAddition] = Field(
        default_factory=list,
        description="Evidence-backed changes to the user's knowledge profile based only on the supplied newly completed picks. Return an empty list when no profile update is warranted or no pending evidence was supplied.",
    )
