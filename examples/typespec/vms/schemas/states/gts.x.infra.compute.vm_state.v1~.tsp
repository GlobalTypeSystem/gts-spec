import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Base VM Power State Type
 *
 * GTS ID: gts.x.infra.compute.vm_state.v1~
 *
 * This is the base type for all VM power states. Each state is a derived GTS type
 * that inherits from this base, enabling backward-compatible state extensions
 * and vendor-specific states.
 */
@jsonSchema("/schemas/gts.x.infra.compute.vm_state.v1~.schema.json")
model VMPowerState {
  /**
   * GTS identifier of the power state type
   */
  @jsonSchema({ "x-gts-ref": "/$id" })
  gtsId: string;

  /**
   * Human-readable description of the power state
   */
  description: string;

  /**
   * Whether this is a transient (in-progress) state
   */
  isTransient?: boolean;

  /**
   * Icon name for UI representation (optional)
   */
  icon?: string;
}
