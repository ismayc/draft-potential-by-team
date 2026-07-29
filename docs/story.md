# Draft value is real. Provable draft skill is rare.

Every June, thirty front offices spend first-round picks like they know
something. Do any of them? This analysis prices every pick slot from the
careers that actually followed, then asks which franchises and which
colleges beat that price. The sample is every draft class from 1989 through
2015: each one with ten full NBA seasons to accumulate a career, scored in
career Win Shares against a slot expectation fit isotonically over picks
1-60. No buckets, no functional form, and every table is produced twice, in
Python and R, and reconciled to numeric tolerance before a word is written.
The companion [interactive viewer](https://ismayc.github.io/draft-potential-by-team/)
holds every lottery and full draft board since 1989.

<div class="tiles">
<div class="tile"><div class="label">The slot gradient</div>
<div class="value">77 &rarr; 2</div>
<div class="sub">Expected career Win Shares at pick 1 versus pick 60.</div></div>
<div class="tile"><div class="label">Best drafting franchise</div>
<div class="value">+489<small> WS</small></div>
<div class="sub">Oklahoma City, above slot expectation across 69 picks.</div></div>
<div class="tile"><div class="label">Intervals crossing zero</div>
<div class="value">27<small> of 30</small></div>
<div class="sub">Most of the league is statistically indistinguishable on drafting skill.</div></div>
<div class="tile"><div class="label">Wake Forest hit rate</div>
<div class="value">70%</div>
<div class="sub">7 of 10 draftees became 10,000-minute NBA players.</div></div>
</div>

<div class="eyebrow beat">The yardstick</div>

## A pick slot is a price

Before anyone gets credit for drafting well, the draft itself has to be
priced. The expectation curve below is a weighted isotonic fit of career
Win Shares over picks 1-60: pick 1 carries an expectation of 77 career Win
Shares, pick 60 carries 2. Everything that follows is measured against this
curve. A player's value is not his career; it is his career minus what his
slot was already worth.

{{fig:fig1_slot_curve|The slot expectation curve. The gradient is steep at the top and nearly flat by the second round, which is why late steals are possible and top-pick "steals" are rare. Hover any pick for its expected career Win Shares.}}

<div class="eyebrow beat">The franchises</div>

## Twenty-seven of thirty error bars cross zero

Rank the franchises by career Win Shares above slot expectation and
Oklahoma City leads at +489 over 69 picks, with San Antonio (+411), the
Lakers (+251), Phoenix (+240), and Golden State (+204) behind. The LA
Clippers sit last at &minus;394. But the honest headline is the intervals:
draft value is heavy-tailed, and 27 of 30 franchise intervals cross zero.
The ordering is the estimate, not a verdict. Ten thousand fan arguments
about "our front office drafts badly" rest on differences this data cannot
certify.

{{fig:fig2_franchises|All 30 franchises by Win Shares above slot expectation, classes 1989-2015. Hover for the 95% interval and the share of drafted minutes each franchise actually kept: drafting well and keeping the player are different skills.}}

<div class="eyebrow beat">The colleges</div>

## Wake Forest, quietly, out-drafted everyone

Flip the question from who drafts to who supplies. Among colleges with 8+
draftees, Wake Forest leads at +323 Win Shares above slot with a 70% hit
rate (Tim Duncan and Chris Paul will do that), ahead of UCLA (+224),
Marquette (+201), Florida (+142), and Xavier (+117). Among high-volume
programs with 15+ draftees, Kentucky has the best hit rate: 25 of 41 picks
(61%) became 10,000-minute NBA players.

{{fig:fig3_colleges|The twelve colleges whose draftees most outplayed their draft slots. Hover for draftee counts and hit rates. Volume and efficiency diverge: powerhouse programs send more players, but the per-pick surplus hides in smaller ones.}}

<div class="eyebrow beat">The steals</div>

## The biggest steal in the sample went first overall

"Steal" usually means a late pick who hit. Priced against slot expectation,
the biggest steal of the era is LeBron James at +200 Win Shares above what
pick 1 already promises. The rest of the top five: Dirk Nowitzki (+170 from
pick 9), Chris Paul (+155 from pick 4), Kobe Bryant (+145 from pick 13),
and Kevin Garnett (+136 from pick 5). A first-overall steal sounds like a
contradiction. It is the strongest possible statement about a career: the
most expensive slot in basketball, and he still quadrupled its price.

| Player | Year | Pick | Drafted by | WS above slot |
| --- | --- | --- | --- | --- |
| LeBron James | 2003 | 1 | Cleveland Cavaliers | +200 |
| Dirk Nowitzki | 1998 | 9 | Milwaukee Bucks | +170 |
| Chris Paul | 2005 | 4 | New Orleans Pelicans | +155 |
| Kobe Bryant | 1996 | 13 | Charlotte Hornets | +145 |
| Kevin Garnett | 1995 | 5 | Minnesota Timberwolves | +136 |

<div class="eyebrow beat">Explore it yourself</div>

## Every lottery, every board, in the browser

The numbers above compress 27 draft classes into a few tables. The
[**interactive draft viewer**](https://ismayc.github.io/draft-potential-by-team/)
is the uncompressed version: every lottery since 1989 with pre-lottery odds
and movement, the full two-round board with career outcomes, colleges, and
teams, in light and dark, timezone-safe, no install. The full tables behind
this page (`colleges.csv`, `teams.csv`, `steals.csv`, `pick_curve.csv`,
each with an `_r.csv` twin from the independent R implementation) ship in
the repo, and the reconcile gate holds the twins equal.
