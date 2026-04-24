import type { AccessTier, RestrictionReason } from '@/types';

interface AccessResult {
  allowed: boolean;
  reason?: RestrictionReason;
}

export function canAccess(feature: string, tier: AccessTier, usage?: unknown): AccessResult {
  if (tier === 'paid') {
    return { allowed: true };
  }

  const usageCount = typeof usage === 'number' ? usage : 0;

  switch (feature) {
    case 'recommendations':
      // Top 10 per profile (usage is index, 0-9 allowed)
      if (usageCount >= 10) {
        return { allowed: false, reason: 'plan_limit' };
      }
      break;

    case 'choice_rows':
      // 20 rows (usage is current count, allow if < 20)
      if (usageCount >= 20) {
        return { allowed: false, reason: 'plan_limit' };
      }
      break;

    case 'choice_notes':
      // Notes on 5 (usage is count of notes, allow if < 5)
      if (usageCount >= 5) {
        return { allowed: false, reason: 'plan_limit' };
      }
      break;

    case 'chat':
      // 3 messages/season (usage is messages sent, allow if < 3)
      if (usageCount >= 3) {
        return { allowed: false, reason: 'plan_limit' };
      }
      break;

    case 'pdf_clean':
      // Only paid tier gets clean PDF (no watermark)
      return { allowed: false, reason: 'plan_limit' };

    default:
      // By default, allow features not explicitly limited here
      // unless they are handled by other logic (phase/data)
      break;
  }

  return { allowed: true };
}
