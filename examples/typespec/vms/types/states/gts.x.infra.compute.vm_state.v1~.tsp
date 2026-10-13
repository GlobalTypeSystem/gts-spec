import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Base VM Power State Type
 *
 * GTS ID: gts.x.infra.compute.vm_state.v1~
 *
 * Each power state is a well-known instance of this final GTS type.
 * Vendors can publish additional state instances without deriving new types.
 */
@jsonSchema("/schemas/gts.x.infra.compute.vm_state.v1~.schema.json")
@extension("x-gts-final", true)
model VMPowerState {
  /**
   * GTS Instance Identifier of the power state
   */
  @extension("x-gts-instance-ref", "/$id")
  id: string;

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
