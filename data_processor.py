"""
ASGARD Dashboard Data Processor
Handles Excel sheet processing, data normalization, and analytics generation.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ProcessingResult:
    """Container for processing results"""
    common_sheet: pd.DataFrame
    week_sheets: Dict[str, pd.DataFrame]
    analytics: Dict
    raw_sheets: Dict[str, pd.DataFrame]
    errors: List[str]


class DataProcessor:
    """Main data processing engine for ASGARD dashboard"""

    def __init__(self):
        self.errors = []
        self.week_columns = {}

    def _normalize_name(self, text: str) -> str:
        """Normalize text for comparison"""
        return re.sub(r"[^a-z0-9]", "", str(text).lower())

    def _parse_numeric(self, value) -> Optional[float]:
        """Parse numeric values from messy strings"""
        if pd.isna(value) or value == '' or value == '-' or value == '—':
            return None
        
        try:
            s = str(value).strip()
            # Handle percent
            if s.endswith('%'):
                return float(s.rstrip('%')) / 100
            # Remove commas
            s = s.replace(',', '')
            return float(s)
        except (ValueError, TypeError):
            return None

    def _detect_week_sections(self, df: pd.DataFrame, metric_type: str) -> Dict[int, Dict[str, str]]:
        """
        Dynamically detect week sections and their columns.
        
        Args:
            df: DataFrame to analyze
            metric_type: 'duel', 'tech', or 'cp'
        
        Returns:
            Dict mapping week number to column names {member, value, avg, tier}
        """
        weeks = {}
        
        if metric_type == 'duel':
            # Look for patterns like "Duel Week 1", "Week 2", etc.
            member_pattern = r"members?\s*(\d+)?"
            week_pattern = r"week\s*([1-9])"
            
            # First pass: find "Members" columns
            member_cols = [c for c in df.columns if re.search(r'members?\s*(\d+)?', c, re.I)]
            
            for col in member_cols:
                # Extract week number if present
                m = re.search(r'members?\s*(\d+)', col, re.I)
                week_num = int(m.group(1)) if m and m.group(1) else None
                
                if week_num is None:
                    # Try to infer from position
                    idx = df.columns.get_loc(col)
                    # Members, Value, Avg, Tier pattern repeats every 4 columns
                    week_num = (idx // 4) + 1
                
                # Find adjacent columns for this week
                idx = df.columns.get_loc(col)
                cols_ahead = list(df.columns[idx:min(idx+5, len(df.columns))])
                
                value_col = None
                avg_col = None
                tier_col = None
                
                for c in cols_ahead[1:]:
                    c_norm = self._normalize_name(c)
                    if 'duel' in c_norm and not value_col:
                        value_col = c
                    elif 'daily' in c_norm or 'average' in c_norm:
                        if not avg_col:
                            avg_col = c
                    elif 'tier' in c_norm and not tier_col:
                        tier_col = c
                
                if value_col:
                    weeks[week_num] = {
                        'member': col,
                        'value': value_col,
                        'avg': avg_col,
                        'tier': tier_col
                    }
        
        elif metric_type == 'tech':
            # Similar pattern for Tech sheet
            member_cols = [c for c in df.columns if re.search(r'members?\s*(\d+)?', c, re.I)]
            
            for col in member_cols:
                m = re.search(r'members?\s*(\d+)', col, re.I)
                week_num = int(m.group(1)) if m and m.group(1) else None
                
                if week_num is None:
                    idx = df.columns.get_loc(col)
                    week_num = (idx // 4) + 1
                
                idx = df.columns.get_loc(col)
                cols_ahead = list(df.columns[idx:min(idx+5, len(df.columns))])
                
                value_col = None
                avg_col = None
                tier_col = None
                
                for c in cols_ahead[1:]:
                    c_norm = self._normalize_name(c)
                    # Match tech contribution values (date ranges or numeric columns)
                    if (re.search(r'apr|may|jun|jul|aug|sep|oct|nov|dec', c_norm) or 
                        re.search(r'\d{1,2}.*\d{1,2}', c_norm)):
                        if not value_col:
                            value_col = c
                    elif 'daily' in c_norm or 'average' in c_norm:
                        if not avg_col:
                            avg_col = c
                    elif 'tier' in c_norm and not tier_col:
                        tier_col = c
                
                if value_col:
                    weeks[week_num] = {
                        'member': col,
                        'value': value_col,
                        'avg': avg_col,
                        'tier': tier_col
                    }
        
        return weeks

    def process_alliance_duel_sheet(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[int, pd.DataFrame]]:
        """
        Process the Alliance Duel sheet.
        
        Returns:
            (unified_members_df, week_dataframes_dict)
        """
        weeks = self._detect_week_sections(df, 'duel')
        
        if not weeks:
            self.errors.append("No week sections detected in Alliance Duel sheet")
            return pd.DataFrame(), {}
        
        all_members = set()
        week_dfs = {}
        member_week_data = {}  # {member: {week_num: {duel, avg, tier}}}
        
        # Extract data for each week
        for week_num, cols in sorted(weeks.items()):
            week_data = []
            
            for idx, row in df.iterrows():
                member = str(row[cols['member']]).strip()
                if not member or pd.isna(row[cols['member']]):
                    continue
                
                all_members.add(member)
                
                duel_val = self._parse_numeric(row[cols['value']])
                avg_val = self._parse_numeric(row[cols['avg']]) if cols['avg'] else None
                tier = str(row[cols['tier']]).strip() if cols['tier'] else None
                
                week_data.append({
                    'Member': member,
                    f'Duel_W{week_num}': duel_val,
                    f'DuelAvg_W{week_num}': avg_val,
                    f'DuelTier_W{week_num}': tier
                })
                
                if member not in member_week_data:
                    member_week_data[member] = {}
                member_week_data[member][week_num] = {
                    'duel': duel_val,
                    'avg': avg_val,
                    'tier': tier
                }
            
            week_dfs[f'Week_{week_num}'] = pd.DataFrame(week_data)
        
        # Create unified dataframe (one row per member)
        unified_data = []
        for member in sorted(all_members):
            row = {'Member': member}
            
            for week_num in sorted(member_week_data[member].keys()):
                week_info = member_week_data[member][week_num]
                row[f'Duel_W{week_num}'] = week_info['duel']
                row[f'DuelAvg_W{week_num}'] = week_info['avg']
                row[f'DuelTier_W{week_num}'] = week_info['tier']
            
            row['TotalDuel'] = sum(
                member_week_data[member].get(w, {}).get('duel', 0) or 0
                for w in member_week_data[member].keys()
            )
            unified_data.append(row)
        
        unified_df = pd.DataFrame(unified_data)
        return unified_df, week_dfs

    def process_tech_sheet(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[int, pd.DataFrame]]:
        """
        Process the Tech sheet.
        
        Returns:
            (unified_members_df, week_dataframes_dict)
        """
        weeks = self._detect_week_sections(df, 'tech')
        
        if not weeks:
            self.errors.append("No week sections detected in Tech sheet")
            return pd.DataFrame(), {}
        
        all_members = set()
        week_dfs = {}
        member_week_data = {}  # {member: {week_num: {tech, avg, tier}}}
        
        # Extract data for each week
        for week_num, cols in sorted(weeks.items()):
            week_data = []
            
            for idx, row in df.iterrows():
                member = str(row[cols['member']]).strip()
                if not member or pd.isna(row[cols['member']]):
                    continue
                
                all_members.add(member)
                
                tech_val = self._parse_numeric(row[cols['value']])
                avg_val = self._parse_numeric(row[cols['avg']]) if cols['avg'] else None
                tier = str(row[cols['tier']]).strip() if cols['tier'] else None
                
                week_data.append({
                    'Member': member,
                    f'Tech_W{week_num}': tech_val,
                    f'TechAvg_W{week_num}': avg_val,
                    f'TechTier_W{week_num}': tier
                })
                
                if member not in member_week_data:
                    member_week_data[member] = {}
                member_week_data[member][week_num] = {
                    'tech': tech_val,
                    'avg': avg_val,
                    'tier': tier
                }
            
            week_dfs[f'Week_{week_num}'] = pd.DataFrame(week_data)
        
        # Create unified dataframe
        unified_data = []
        for member in sorted(all_members):
            row = {'Member': member}
            
            for week_num in sorted(member_week_data[member].keys()):
                week_info = member_week_data[member][week_num]
                row[f'Tech_W{week_num}'] = week_info['tech']
                row[f'TechAvg_W{week_num}'] = week_info['avg']
                row[f'TechTier_W{week_num}'] = week_info['tier']
            
            row['TotalTech'] = sum(
                member_week_data[member].get(w, {}).get('tech', 0) or 0
                for w in member_week_data[member].keys()
            )
            unified_data.append(row)
        
        unified_df = pd.DataFrame(unified_data)
        return unified_df, week_dfs

    def process_cp_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process the CP Check sheet.
        
        Returns:
            DataFrame with member CP data
        """
        # Find member column
        member_col = None
        for c in df.columns:
            if 'member' in self._normalize_name(c):
                member_col = c
                break
        
        if not member_col:
            self.errors.append("No member column found in CP sheet")
            return pd.DataFrame()
        
        # Find CP-related columns
        cp_cols = [c for c in df.columns if 'cp' in self._normalize_name(c) or '23' in str(c)]
        
        result = []
        for idx, row in df.iterrows():
            member = str(row[member_col]).strip()
            if not member or pd.isna(row[member_col]):
                continue
            
            data = {'Member': member}
            
            # Extract 23 days growth (main metric)
            for c in cp_cols:
                c_norm = self._normalize_name(c)
                if '23' in str(c) or 'growth' in c_norm:
                    data['CP_23d_Growth'] = self._parse_numeric(row[c])
                    break
            
            # Also capture tier if present
            for c in df.columns:
                if 'tier' in self._normalize_name(c):
                    data['CP_Tier'] = str(row[c]).strip()
                    break
            
            result.append(data)
        
        return pd.DataFrame(result)

    def merge_sheets(self, duel_df: pd.DataFrame, tech_df: pd.DataFrame, cp_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge all three processed sheets into a single common sheet.
        
        Args:
            duel_df: Processed Alliance Duel sheet
            tech_df: Processed Tech sheet
            cp_df: Processed CP Check sheet
        
        Returns:
            Unified common sheet with all members and their metrics
        """
        # Start with duel data
        merged = duel_df.copy() if len(duel_df) > 0 else pd.DataFrame()
        
        # Merge tech data
        if len(tech_df) > 0:
            if len(merged) == 0:
                merged = tech_df.copy()
            else:
                merged = pd.merge(merged, tech_df, on='Member', how='outer')
        
        # Merge CP data
        if len(cp_df) > 0:
            if len(merged) == 0:
                merged = cp_df.copy()
            else:
                merged = pd.merge(merged, cp_df, on='Member', how='outer')
        
        # Clean up: ensure unique members
        if len(merged) > 0:
            merged = merged.drop_duplicates(subset=['Member'])
            merged = merged.sort_values('Member').reset_index(drop=True)
        
        return merged

    def generate_analytics(self, common_sheet: pd.DataFrame) -> Dict:
        """
        Generate analytics from the common sheet.
        
        Returns:
            Dict with analytics data
        """
        if len(common_sheet) == 0:
            return {}
        
        # Create a copy to avoid modifying the original
        df = common_sheet.copy()
        
        analytics = {}
        
        # Basic stats
        analytics['total_members'] = len(df)
        
        # Total contributions - use .sum() directly with fillna
        total_duel = df['TotalDuel'].fillna(0).sum() if 'TotalDuel' in df.columns else 0
        total_tech = df['TotalTech'].fillna(0).sum() if 'TotalTech' in df.columns else 0
        total_cp = df['CP_23d_Growth'].fillna(0).sum() if 'CP_23d_Growth' in df.columns else 0
        
        analytics['total_duel'] = float(total_duel)
        analytics['total_tech'] = float(total_tech)
        analytics['total_cp_growth'] = float(total_cp)
        
        # Bottom 20 performers (combined metric)
        df['CombinedScore'] = (
            (df['TotalDuel'].fillna(0) * 1000) +
            (df['TotalTech'].fillna(0) * 1) +
            (df['CP_23d_Growth'].fillna(0) * 100)
        )
        
        bottom_20 = df.nsmallest(20, 'CombinedScore')[[
            'Member', 'TotalDuel', 'TotalTech', 'CP_23d_Growth', 'CombinedScore'
        ]].copy()
        bottom_20 = bottom_20.fillna(0).to_dict('records')
        analytics['bottom_20'] = bottom_20
        
        # Lowest contributors by metric
        if 'TotalDuel' in df.columns:
            lowest_duel = df.nsmallest(10, 'TotalDuel')[['Member', 'TotalDuel']].copy()
            analytics['lowest_duel'] = lowest_duel.fillna(0).to_dict('records')
        
        if 'TotalTech' in df.columns:
            lowest_tech = df.nsmallest(10, 'TotalTech')[['Member', 'TotalTech']].copy()
            analytics['lowest_tech'] = lowest_tech.fillna(0).to_dict('records')
        
        if 'CP_23d_Growth' in df.columns:
            least_active_cp = df.nsmallest(10, 'CP_23d_Growth')[['Member', 'CP_23d_Growth']].copy()
            analytics['least_active_cp'] = least_active_cp.fillna(0).to_dict('records')
        
        # Top performers
        if 'TotalDuel' in df.columns:
            top_duel = df.nlargest(10, 'TotalDuel')[['Member', 'TotalDuel']].copy()
            analytics['top_duel'] = top_duel.fillna(0).to_dict('records')
        
        if 'TotalTech' in df.columns:
            top_tech = df.nlargest(10, 'TotalTech')[['Member', 'TotalTech']].copy()
            analytics['top_tech'] = top_tech.fillna(0).to_dict('records')
        
        if 'CP_23d_Growth' in df.columns:
            top_cp_growth = df.nlargest(10, 'CP_23d_Growth')[['Member', 'CP_23d_Growth']].copy()
            analytics['top_cp_growth'] = top_cp_growth.fillna(0).to_dict('records')
        
        return analytics

    def process_excel_file(self, file_path: str) -> ProcessingResult:
        """
        Main entry point: Process an Excel file with all sheets.
        
        Args:
            file_path: Path to the Excel file
        
        Returns:
            ProcessingResult with all processed data and analytics
        """
        self.errors = []
        
        try:
            # Read all sheets
            xls = pd.ExcelFile(file_path)
            raw_sheets = {}
            
            for sheet_name in xls.sheet_names:
                raw_sheets[sheet_name] = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Process each sheet
            duel_df, duel_weeks = self.process_alliance_duel_sheet(
                raw_sheets.get('Alliance duel', pd.DataFrame())
            )
            
            tech_df, tech_weeks = self.process_tech_sheet(
                raw_sheets.get('Tech', pd.DataFrame())
            )
            
            cp_df = self.process_cp_sheet(
                raw_sheets.get('CP check', pd.DataFrame())
            )
            
            # Merge all data
            common_sheet = self.merge_sheets(duel_df, tech_df, cp_df)
            
            # Generate analytics
            analytics = self.generate_analytics(common_sheet)
            
            # Combine week sheets
            week_sheets = {**duel_weeks, **tech_weeks}
            
            return ProcessingResult(
                common_sheet=common_sheet,
                week_sheets=week_sheets,
                analytics=analytics,
                raw_sheets=raw_sheets,
                errors=self.errors
            )
        
        except Exception as e:
            import traceback
            self.errors.append(f"Error processing file: {str(e)}")
            self.errors.append(traceback.format_exc())
            return ProcessingResult(
                common_sheet=pd.DataFrame(),
                week_sheets={},
                analytics={},
                raw_sheets={},
                errors=self.errors
            )
