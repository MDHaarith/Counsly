import { canAccess } from './access';

describe('canAccess', () => {
  describe('Paid Tier', () => {
    const tier = 'paid';

    it('allows all features regardless of usage', () => {
      expect(canAccess('recommendations', tier, 100)).toEqual({ allowed: true });
      expect(canAccess('choice_rows', tier, 500)).toEqual({ allowed: true });
      expect(canAccess('chat', tier, 1000)).toEqual({ allowed: true });
      expect(canAccess('pdf_clean', tier)).toEqual({ allowed: true });
    });
  });

  describe('Free Tier', () => {
    const tier = 'free';

    describe('recommendations', () => {
      it('allows access to top 10 recommendations (0-9 index)', () => {
        expect(canAccess('recommendations', tier, 0)).toEqual({ allowed: true });
        expect(canAccess('recommendations', tier, 9)).toEqual({ allowed: true });
      });

      it('denies access to recommendations beyond top 10', () => {
        expect(canAccess('recommendations', tier, 10)).toEqual({
          allowed: false,
          reason: 'plan_limit',
        });
        expect(canAccess('recommendations', tier, 11)).toEqual({
          allowed: false,
          reason: 'plan_limit',
        });
      });
    });

    describe('choice_rows', () => {
      it('allows up to 20 choice rows', () => {
        expect(canAccess('choice_rows', tier, 0)).toEqual({ allowed: true });
        expect(canAccess('choice_rows', tier, 19)).toEqual({ allowed: true });
      });

      it('denies access when 20 or more rows are used', () => {
        expect(canAccess('choice_rows', tier, 20)).toEqual({
          allowed: false,
          reason: 'plan_limit',
        });
        expect(canAccess('choice_rows', tier, 21)).toEqual({
          allowed: false,
          reason: 'plan_limit',
        });
      });
    });

    describe('choice_notes', () => {
      it('allows notes on up to 5 choices', () => {
        expect(canAccess('choice_notes', tier, 0)).toEqual({ allowed: true });
        expect(canAccess('choice_notes', tier, 4)).toEqual({ allowed: true });
      });

      it('denies access when 5 or more notes are used', () => {
        expect(canAccess('choice_notes', tier, 5)).toEqual({
          allowed: false,
          reason: 'plan_limit',
        });
      });
    });

    describe('chat', () => {
      it('allows up to 3 messages per season', () => {
        expect(canAccess('chat', tier, 0)).toEqual({ allowed: true });
        expect(canAccess('chat', tier, 2)).toEqual({ allowed: true });
      });

      it('denies access when 3 or more messages are sent', () => {
        expect(canAccess('chat', tier, 3)).toEqual({
          allowed: false,
          reason: 'plan_limit',
        });
      });
    });

    describe('pdf_clean', () => {
      it('always denies clean PDF for free tier', () => {
        expect(canAccess('pdf_clean', tier)).toEqual({
          allowed: false,
          reason: 'plan_limit',
        });
      });
    });

    describe('unknown features', () => {
      it('allows access to unknown features by default', () => {
        expect(canAccess('news', tier)).toEqual({ allowed: true });
        expect(canAccess('onboarding', tier)).toEqual({ allowed: true });
      });
    });

    describe('usage parameter edge cases', () => {
      it('treats non-number usage as 0', () => {
        expect(canAccess('chat', tier, undefined)).toEqual({ allowed: true });
        expect(canAccess('chat', tier, 'invalid')).toEqual({ allowed: true });
        expect(canAccess('chat', tier, null)).toEqual({ allowed: true });
      });
    });
  });
});
