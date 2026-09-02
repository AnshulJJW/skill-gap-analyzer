/* The one supportive line shown beside the score.

   A gap report is, by construction, a list of things you cannot do yet.
   Read cold that is discouraging, and discouraged people close the tab
   instead of learning anything. One plain sentence fixes it.

   Rules, deliberately narrow:
   - Never judge the person. The gap is a fact about a job market, not about
     them, and the wording keeps that distinction.
   - Never exaggerate. "You are close" when someone matches 12% would be a
     lie, and a tool whose numbers are its whole argument cannot afford one.
   - One sentence. Anything longer reads as a motivational poster.

   Pure and separate from the view so the bands can be tested without a
   browser. */

/** Coverage bands, as fractions. Chosen to match what the number means:
 *  below 0.35 there is real ground to cover, above 0.7 the remaining gap is
 *  a handful of skills. */
const NEAR = 0.7;
const MID = 0.35;

export function encouragement(coverage, missingCount) {
  if (missingCount === 0) {
    return "Nothing missing here. Worth checking a second role to compare.";
  }
  if (coverage >= NEAR) {
    return "You are already close. A couple of these would cover most of the gap.";
  }
  if (coverage >= MID) {
    return "Good base to build on. Take these one at a time, starting at the top.";
  }
  return "Plenty here is learnable. Start with the first item and work down — the order is chosen for you.";
}

/** The single-posting version. One job is a narrower claim than a market, so
 *  the wording does not generalise from it. */
export function encouragementForJD(coverage, missingCount) {
  if (missingCount === 0) {
    return "You match everything this posting asks for.";
  }
  if (coverage >= NEAR) {
    return "You match most of this posting. The rest is a short list.";
  }
  if (coverage >= MID) {
    return "A solid overlap. Focus on the ones the wider market wants too.";
  }
  return "This one asks for a lot. The market column shows which parts are worth your time anyway.";
}
