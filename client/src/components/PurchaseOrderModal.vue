<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div
          ref="dialogRef"
          class="modal-container po-modal-container"
          role="dialog"
          aria-modal="true"
          aria-labelledby="po-modal-title"
          tabindex="-1"
          @click.stop
        >
          <div class="modal-header">
            <h3 id="po-modal-title" class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" :aria-label="t('common.close')" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
              <div class="item-meta">
                {{ t('purchaseOrder.sku') }}: {{ backlogItem.item_sku }} &middot;
                {{ t('purchaseOrder.orderId') }}: {{ backlogItem.order_id }} &middot;
                {{ t('purchaseOrder.shortage') }}: {{ shortage }}
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
              <div v-else-if="error" class="error" role="alert">{{ error }}</div>
              <dl v-else-if="po" class="info-grid">
                <div class="info-item">
                  <dt class="info-label">{{ t('purchaseOrder.poNumber') }}</dt>
                  <dd class="info-value mono">{{ po.id }}</dd>
                </div>
                <div class="info-item">
                  <dt class="info-label">{{ t('purchaseOrder.status') }}</dt>
                  <dd class="info-value"><span class="badge info">{{ po.status }}</span></dd>
                </div>
                <div class="info-item">
                  <dt class="info-label">{{ t('purchaseOrder.supplier') }}</dt>
                  <dd class="info-value">{{ po.supplier_name }}</dd>
                </div>
                <div class="info-item">
                  <dt class="info-label">{{ t('purchaseOrder.quantity') }}</dt>
                  <dd class="info-value">{{ po.quantity }}</dd>
                </div>
                <div class="info-item">
                  <dt class="info-label">{{ t('purchaseOrder.unitCost') }}</dt>
                  <dd class="info-value">{{ formatMoney(po.unit_cost) }}</dd>
                </div>
                <div class="info-item">
                  <dt class="info-label">{{ t('purchaseOrder.total') }}</dt>
                  <dd class="info-value"><strong>{{ formatMoney(po.quantity * po.unit_cost) }}</strong></dd>
                </div>
                <div class="info-item">
                  <dt class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</dt>
                  <dd class="info-value">{{ formatDate(po.expected_delivery_date) }}</dd>
                </div>
                <div class="info-item">
                  <dt class="info-label">{{ t('purchaseOrder.createdDate') }}</dt>
                  <dd class="info-value">{{ formatDate(po.created_date) }}</dd>
                </div>
                <div v-if="po.notes" class="info-item full-row">
                  <dt class="info-label">{{ t('purchaseOrder.notes') }}</dt>
                  <dd class="info-value notes">{{ po.notes }}</dd>
                </div>
              </dl>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" novalidate @submit.prevent="submit">
              <div class="form-group">
                <label for="po-supplier">{{ t('purchaseOrder.supplier') }}</label>
                <input id="po-supplier" ref="firstFieldRef" v-model="form.supplier_name" type="text" required />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model.number="form.quantity" type="number" min="1" step="1" required />
                </div>
                <div class="form-group">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCostUsd') }}</label>
                  <input id="po-unit-cost" v-model.number="form.unit_cost" type="number" min="0" step="0.01" required />
                </div>
              </div>
              <div class="form-group">
                <label for="po-delivery">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input id="po-delivery" v-model="form.expected_delivery_date" type="date" required />
              </div>
              <div class="form-group">
                <label for="po-notes">{{ t('purchaseOrder.notes') }} ({{ t('purchaseOrder.optional') }})</label>
                <textarea id="po-notes" v-model="form.notes" rows="3"></textarea>
              </div>
              <div v-if="error" class="error" role="alert">{{ error }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode !== 'view'"
              type="submit"
              form="po-form"
              class="btn-primary"
              :disabled="!isValid || submitting"
            >
              {{ submitting ? t('purchaseOrder.creating') : t('purchaseOrder.create') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: { type: String, default: 'create' }
})

const emit = defineEmits(['close', 'po-created'])

const { t, translateProductName } = useI18n()

const dialogRef = ref(null)
const firstFieldRef = ref(null)
const po = ref(null)
const loading = ref(false)
const submitting = ref(false)
const error = ref(null)
const form = ref({ supplier_name: '', quantity: 1, unit_cost: null, expected_delivery_date: '', notes: '' })

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return Math.max(props.backlogItem.quantity_needed - props.backlogItem.quantity_available, 0)
})

const isValid = computed(() =>
  form.value.supplier_name.trim() !== '' &&
  Number.isInteger(form.value.quantity) && form.value.quantity > 0 &&
  typeof form.value.unit_cost === 'number' && form.value.unit_cost >= 0 &&
  form.value.expected_delivery_date !== ''
)

// PO amounts are stored in USD and the unit cost is entered in USD, so show USD
// regardless of the UI currency; converting only the display would mislead.
const formatMoney = (amount) => formatCurrencyWithDecimals(amount, 'USD', 2)

const formatDate = (value) => {
  if (!value) return 'N/A'
  const date = new Date(value)
  if (isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const close = () => emit('close')

const onKeydown = (e) => {
  if (e.key === 'Escape') close()
}

// Monotonic id so a slow response for a previously opened item can't overwrite the current one.
let loadSeq = 0

const loadPO = async () => {
  const seq = ++loadSeq
  loading.value = true
  error.value = null
  po.value = null
  try {
    const data = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
    if (seq === loadSeq) po.value = data
  } catch (err) {
    if (seq !== loadSeq) return
    error.value = err.response?.status === 404 ? t('purchaseOrder.notFound') : t('purchaseOrder.loadFailed')
    console.error('Failed to load purchase order:', err)
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

const submit = async () => {
  if (!isValid.value || submitting.value) return
  submitting.value = true
  error.value = null
  try {
    const created = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplier_name.trim(),
      quantity: form.value.quantity,
      unit_cost: form.value.unit_cost,
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes.trim() || null
    })
    emit('po-created', created)
  } catch (err) {
    const status = err.response?.status
    error.value = status === 400 ? t('purchaseOrder.alreadyExists')
      : status === 404 ? t('purchaseOrder.itemNotFound')
      : t('purchaseOrder.createFailed')
    console.error('Failed to create purchase order:', err)
  } finally {
    submitting.value = false
  }
}

// Reset state and (in view mode) fetch each time the modal opens or targets a different item;
// the component stays mounted, so stale form/PO data would otherwise carry over.
watch(
  () => [props.isOpen, props.backlogItem?.id, props.mode],
  async ([open]) => {
    if (!open || !props.backlogItem) {
      document.removeEventListener('keydown', onKeydown)
      return
    }
    document.addEventListener('keydown', onKeydown)
    error.value = null
    if (props.mode === 'view') {
      loadPO()
    } else {
      form.value = {
        supplier_name: '',
        quantity: shortage.value || 1,
        unit_cost: null,
        expected_delivery_date: '',
        notes: ''
      }
    }
    await nextTick()
    // Focus the first field in create mode, otherwise the dialog itself, so Escape/Tab act inside it.
    ;(props.mode === 'view' ? dialogRef.value : firstFieldRef.value)?.focus()
  },
  { immediate: true }
)

onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.po-modal-container {
  max-width: 560px;
  outline: none;
}

.item-summary {
  padding-bottom: var(--space-4);
  margin-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.item-name {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

.item-meta {
  margin-top: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.form-group label,
.info-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.form-group textarea {
  resize: vertical;
  min-height: 72px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  margin: 0;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.info-item.full-row {
  grid-column: 1 / -1;
}

.info-value {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text);
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
}

.info-value.notes {
  white-space: pre-wrap;
}

.error {
  margin: 0;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
