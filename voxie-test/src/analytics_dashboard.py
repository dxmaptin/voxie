"""
Call Analytics Dashboard - CLI Version
Real-time monitoring of call costs, quality, and performance
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from supabase_client import supabase_client


class AnalyticsDashboard:
    """Simple CLI dashboard for call analytics"""

    @staticmethod
    async def show_overview():
        """Show high-level overview of all metrics"""
        print("\n" + "="*80)
        print(" 📊 CALL ANALYTICS DASHBOARD")
        print("="*80 + "\n")

        # Today's stats
        today = datetime.now(timezone.utc).date()
        result = supabase_client.client.table('daily_cost_summary')\
            .select('*')\
            .eq('date', str(today))\
            .execute()

        if result.data:
            stats = result.data[0]
            print(f"📅 TODAY ({today})")
            print(f"   Calls: {stats.get('total_calls', 0)}")
            print(f"   Completed: {stats.get('completed_calls', 0)}")
            print(f"   Total Tokens: {stats.get('total_tokens', 0):,}")
            print(f"   Total Cost: ${stats.get('total_cost_usd', 0):.2f}")
            print(f"   Avg Rating: {stats.get('avg_rating', 0) or 'N/A'}")
        else:
            print(f"📅 TODAY ({today})")
            print("   No calls yet today")

        print()

        # Active calls
        active = supabase_client.client.table('active_calls').select('*').execute()
        print(f"🟢 ACTIVE CALLS: {len(active.data)}")
        if active.data:
            for call in active.data[:5]:
                print(f"   • {call['agent_name'] or 'Unknown'} | "
                      f"{call['duration_so_far_seconds']}s | "
                      f"${call['cost_so_far_usd']:.4f}")
        print()

        # Last 7 days trend
        result = supabase_client.client.table('daily_cost_summary')\
            .select('*')\
            .order('date', desc=True)\
            .limit(7)\
            .execute()

        print("📈 LAST 7 DAYS")
        total_week_cost = 0
        for day in result.data:
            total_week_cost += day.get('total_cost_usd', 0)
            print(f"   {day['date']}: "
                  f"{day.get('total_calls', 0)} calls | "
                  f"${day.get('total_cost_usd', 0):.2f}")

        print(f"\n   💰 Week Total: ${total_week_cost:.2f}")
        print()

    @staticmethod
    async def show_agent_performance():
        """Show agent performance leaderboard"""
        print("\n" + "="*80)
        print(" 🏆 AGENT PERFORMANCE LEADERBOARD (Last 30 Days)")
        print("="*80 + "\n")

        result = supabase_client.client.table('agent_performance').select('*').execute()

        if not result.data:
            print("   No agent data available\n")
            return

        print(f"{'Agent Name':<30} {'Calls':>8} {'Avg Cost':>10} {'Rating':>8} {'Sales':>8}")
        print("-" * 80)

        for agent in result.data[:10]:
            print(f"{agent['name'][:30]:<30} "
                  f"{agent.get('total_calls', 0):>8} "
                  f"${agent.get('avg_cost_per_call', 0):>9.2f} "
                  f"{agent.get('avg_rating', 0) or 'N/A':>8} "
                  f"{agent.get('sales_count', 0):>8}")

        print()

    @staticmethod
    async def show_expensive_calls(limit: int = 10):
        """Show most expensive calls"""
        print("\n" + "="*80)
        print(f" 💸 TOP {limit} MOST EXPENSIVE CALLS")
        print("="*80 + "\n")

        # Query for expensive calls
        query = """
        SELECT
          cs.id,
          cs.session_id,
          cs.started_at,
          cs.duration_seconds,
          a.name as agent_name,
          SUM(tu.total_tokens) as total_tokens,
          SUM(tu.total_cost_usd) as total_cost
        FROM call_sessions cs
        LEFT JOIN agents a ON cs.agent_id = a.id
        LEFT JOIN token_usage tu ON tu.session_id = cs.id
        WHERE cs.started_at >= NOW() - INTERVAL '7 days'
        GROUP BY cs.id, a.name
        ORDER BY total_cost DESC
        LIMIT $1
        """

        # Since we can't run raw SQL easily, we'll fetch and process
        sessions = supabase_client.client.table('call_sessions')\
            .select('id, session_id, started_at, duration_seconds')\
            .order('started_at', desc=True)\
            .limit(100)\
            .execute()

        # Get token usage for each
        call_costs = []
        for session in sessions.data:
            tokens = supabase_client.client.table('token_usage')\
                .select('total_tokens, total_cost_usd')\
                .eq('call_session_id', session['id'])\
                .execute()

            if tokens.data:
                total_cost = sum(t['total_cost_usd'] for t in tokens.data)
                total_tokens = sum(t['total_tokens'] for t in tokens.data)
                call_costs.append({
                    **session,
                    'total_cost': total_cost,
                    'total_tokens': total_tokens
                })

        # Sort by cost
        call_costs.sort(key=lambda x: x['total_cost'], reverse=True)

        print(f"{'Date':<20} {'Duration':>10} {'Tokens':>12} {'Cost':>10}")
        print("-" * 80)

        for call in call_costs[:limit]:
            date_str = call['started_at'][:19] if call['started_at'] else 'N/A'
            duration = call.get('duration_seconds', 0) or 0
            print(f"{date_str:<20} "
                  f"{duration:>10}s "
                  f"{call.get('total_tokens', 0):>12,} "
                  f"${call.get('total_cost', 0):>9.2f}")

        print()

    @staticmethod
    async def show_recent_calls(limit: int = 10):
        """Show recent calls with details"""
        print("\n" + "="*80)
        print(f" 📞 RECENT CALLS (Last {limit})")
        print("="*80 + "\n")

        result = supabase_client.client.table('call_sessions')\
            .select('*, agents(name)')\
            .order('started_at', desc=True)\
            .limit(limit)\
            .execute()

        if not result.data:
            print("   No recent calls\n")
            return

        for call in result.data:
            agent_name = call.get('agents', {}).get('name', 'Unknown') if call.get('agents') else 'Unknown'
            status_emoji = {
                'completed': '✅',
                'active': '🟢',
                'failed': '❌',
                'abandoned': '⚠️'
            }.get(call['call_status'], '❓')

            print(f"{status_emoji} {call['started_at'][:19]}")
            print(f"   Agent: {agent_name}")
            print(f"   Status: {call['call_status']}")
            if call.get('duration_seconds'):
                print(f"   Duration: {call['duration_seconds']}s")
            if call.get('call_rating'):
                print(f"   Rating: {call['call_rating']}/10")
            print()

    @staticmethod
    async def show_cost_breakdown():
        """Show cost breakdown by model and interaction type"""
        print("\n" + "="*80)
        print(" 💰 COST BREAKDOWN (Last 7 Days)")
        print("="*80 + "\n")

        # By model
        result = supabase_client.client.rpc('get_cost_by_model', {
            'days': 7
        }).execute() if hasattr(supabase_client.client, 'rpc') else None

        if not result or not result.data:
            # Fallback: manual aggregation
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            tokens = supabase_client.client.table('token_usage')\
                .select('model, total_tokens, total_cost_usd, interaction_type')\
                .gte('recorded_at', week_ago)\
                .execute()

            # Aggregate by model
            by_model = {}
            by_type = {}

            for token in tokens.data:
                model = token['model']
                itype = token['interaction_type']

                if model not in by_model:
                    by_model[model] = {'tokens': 0, 'cost': 0, 'count': 0}
                by_model[model]['tokens'] += token['total_tokens']
                by_model[model]['cost'] += token['total_cost_usd']
                by_model[model]['count'] += 1

                if itype not in by_type:
                    by_type[itype] = {'tokens': 0, 'cost': 0, 'count': 0}
                by_type[itype]['tokens'] += token['total_tokens']
                by_type[itype]['cost'] += token['total_cost_usd']
                by_type[itype]['count'] += 1

            print("📊 BY MODEL:")
            for model, data in sorted(by_model.items(), key=lambda x: x[1]['cost'], reverse=True):
                print(f"   {model:<25} {data['count']:>6} calls | "
                      f"{data['tokens']:>12,} tokens | ${data['cost']:>8.2f}")

            print("\n📊 BY INTERACTION TYPE:")
            for itype, data in sorted(by_type.items(), key=lambda x: x[1]['cost'], reverse=True):
                print(f"   {itype:<25} {data['count']:>6} calls | "
                      f"{data['tokens']:>12,} tokens | ${data['cost']:>8.2f}")

        print()


async def main_menu():
    """Main dashboard menu"""
    while True:
        print("\n" + "="*80)
        print(" 📊 CALL ANALYTICS DASHBOARD - MENU")
        print("="*80)
        print("\n1. Overview")
        print("2. Agent Performance")
        print("3. Recent Calls")
        print("4. Expensive Calls")
        print("5. Cost Breakdown")
        print("6. Refresh All")
        print("0. Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == '1':
            await AnalyticsDashboard.show_overview()
        elif choice == '2':
            await AnalyticsDashboard.show_agent_performance()
        elif choice == '3':
            await AnalyticsDashboard.show_recent_calls()
        elif choice == '4':
            await AnalyticsDashboard.show_expensive_calls()
        elif choice == '5':
            await AnalyticsDashboard.show_cost_breakdown()
        elif choice == '6':
            await AnalyticsDashboard.show_overview()
            await AnalyticsDashboard.show_agent_performance()
            await AnalyticsDashboard.show_recent_calls()
        elif choice == '0':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("\n❌ Invalid option\n")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("\n🚀 Starting Call Analytics Dashboard...")
    print("✅ Supabase connected\n")

    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard closed\n")
        sys.exit(0)
