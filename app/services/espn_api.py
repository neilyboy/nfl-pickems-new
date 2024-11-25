import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from dateutil import tz

logger = logging.getLogger(__name__)

class ESPNApiService:
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    ALT_URL = "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl"
    
    @staticmethod
    def get_current_nfl_week() -> Dict:
        """Get the current NFL week information"""
        try:
            logger.info("Fetching current NFL week from ESPN API...")
            params = {
                'lang': 'en',
                'region': 'us',
                'calendartype': 'blacklist',
                'limit': 100
            }
            
            # Try both URLs with proper error handling
            urls = [
                f"{ESPNApiService.ALT_URL}/scoreboard",
                f"{ESPNApiService.BASE_URL}/scoreboard"
            ]
            
            data = None
            last_error = None
            
            for url in urls:
                try:
                    logger.info(f"Trying URL: {url}")
                    response = requests.get(url, params=params, timeout=5)  # shorter timeout for current week
                    response.raise_for_status()
                    data = response.json()
                    if data:
                        logger.info(f"Successfully fetched data from {url}")
                        break
                except requests.exceptions.Timeout:
                    last_error = "ESPN API request timed out"
                    logger.error(f"{last_error} for {url}")
                    continue
                except requests.exceptions.RequestException as e:
                    last_error = f"ESPN API request failed: {str(e)}"
                    logger.error(f"{last_error} for {url}")
                    continue
                except ValueError as e:
                    last_error = f"Failed to parse ESPN API response as JSON: {str(e)}"
                    logger.error(f"{last_error} for {url}")
                    continue
            
            if not data:
                logger.error("Failed to fetch data from all URLs, using default week info")
                return {
                    'week': 12,  # Current week as of Nov 24, 2023
                    'season_type': 2,  # Regular season
                    'year': datetime.now().year
                }
            
            # Check if we're in the offseason
            calendar = data.get('leagues', [{}])[0].get('calendar', [])
            current_season_type = data.get('season', {}).get('type', 2)
            
            # If we're in the offseason (no current games), default to week 1 of next season
            if not data.get('events'):
                logger.info("No current games found - might be offseason")
                current_year = datetime.now().year
                next_season_start = datetime(current_year, 9, 1)  # Approximate NFL season start
                
                if datetime.now() < next_season_start:
                    year = current_year - 1  # Use previous year if before September
                else:
                    year = current_year
                
                return {
                    'week': 1,
                    'season_type': 2,  # Regular season
                    'year': year
                }
            
            week_info = {
                'week': data.get('week', {}).get('number', 12),  # Default to current week if not found
                'season_type': current_season_type,
                'year': data.get('season', {}).get('year', datetime.now().year)
            }
            
            logger.info(f"Current NFL week info: {week_info}")
            return week_info
            
        except Exception as e:
            logger.error(f"Error fetching current NFL week: {str(e)}")
            # Default to current week if there's an error
            return {
                'week': 12,  # Current week as of Nov 24, 2023
                'season_type': 2,
                'year': datetime.now().year
            }

    @staticmethod
    def get_week_games(week: int, season_type: int = 2, year: Optional[int] = None) -> List[Dict]:
        """
        Get all games for a specific week
        
        Args:
            week: Week number (1-18 for regular season)
            season_type: 1=preseason, 2=regular season, 3=postseason
            year: NFL season year (e.g., 2024 for the 2024-25 season)
        """
        if not year:
            year = datetime.now().year
            
        try:
            logger.info(f"Fetching games for week {week}, season_type {season_type}, year {year}")
            params = {
                'lang': 'en',
                'region': 'us',
                'calendartype': 'blacklist',
                'limit': 100,
                'seasontype': season_type,
                'week': week,
                'dates': year
            }
            
            # Try both URLs with proper error handling
            urls = [
                f"{ESPNApiService.ALT_URL}/scoreboard",
                f"{ESPNApiService.BASE_URL}/scoreboard"
            ]
            
            data = None
            last_error = None
            
            for url in urls:
                try:
                    logger.info(f"Trying URL: {url}")
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    if data and data.get('events'):
                        logger.info(f"Successfully fetched data from {url}")
                        break
                except requests.exceptions.Timeout:
                    last_error = "ESPN API request timed out"
                    logger.error(f"{last_error} for {url}")
                    continue
                except requests.exceptions.RequestException as e:
                    last_error = f"ESPN API request failed: {str(e)}"
                    logger.error(f"{last_error} for {url}")
                    continue
                except ValueError as e:
                    last_error = f"Failed to parse ESPN API response as JSON: {str(e)}"
                    logger.error(f"{last_error} for {url}")
                    continue
            
            if not data:
                logger.error("Failed to fetch data from all URLs")
                if last_error:
                    logger.error(f"Last error: {last_error}")
                return []
            
            # Log the raw response for debugging
            logger.info(f"Raw response data: {data}")
            
            games = []
            events = data.get('events', [])
            logger.info(f"Found {len(events)} games")
            
            for event in events:
                try:
                    game_data = ESPNApiService.parse_game_data(event)
                    if game_data:  # Only add if we successfully parsed the game
                        games.append(game_data)
                        logger.info(f"Successfully parsed game: {game_data.get('game_id')} - {game_data.get('home_team', {}).get('display_name')} vs {game_data.get('away_team', {}).get('display_name')}")
                except Exception as e:
                    logger.error(f"Error parsing game data for event {event.get('id', 'unknown')}: {str(e)}")
                    continue
            
            return games
            
        except Exception as e:
            logger.error(f"Error fetching week {week} games: {str(e)}")
            return []

    @staticmethod
    def parse_game_status(event):
        """Parse game status from ESPN API event data."""
        status = event.get('status', {}).get('type', {}).get('name', '')
        detail = event.get('status', {}).get('type', {}).get('detail', '')
        
        # Map ESPN status to our internal status
        status_map = {
            'STATUS_SCHEDULED': 'Scheduled',
            'STATUS_IN_PROGRESS': 'In Progress',
            'STATUS_HALFTIME': 'Halftime',
            'STATUS_END_PERIOD': 'End Period',
            'STATUS_FINAL': 'Final',
            'STATUS_FINAL_OVERTIME': 'Final OT',
            'STATUS_POSTPONED': 'Postponed',
            'STATUS_CANCELED': 'Canceled',
            'STATUS_SUSPENDED': 'Suspended',
            'STATUS_DELAYED': 'Delayed'
        }
        
        # Check if it's a final status from the detail field
        if detail:
            detail_lower = detail.lower()
            if 'final' in detail_lower:
                if any(x in detail_lower for x in ['ot', 'overtime']):
                    return 'Final OT'
                return 'Final'
        
        return status_map.get(status, status)

    @staticmethod
    def determine_winner(event):
        """Determine winner from ESPN API event data."""
        status = event.get('status', {}).get('type', {}).get('name', '')
        detail = event.get('status', {}).get('type', {}).get('detail', '')
        
        # Check if game is final (including overtime)
        is_final = (
            status in ['STATUS_FINAL', 'STATUS_FINAL_OVERTIME'] or
            (detail and 'final' in detail.lower())
        )
        
        if not is_final:
            return None
            
        competitors = event.get('competitions', [{}])[0].get('competitors', [])
        if len(competitors) != 2:
            return None
            
        home_team = next((team for team in competitors if team.get('homeAway') == 'home'), None)
        away_team = next((team for team in competitors if team.get('homeAway') == 'away'), None)
        
        if not home_team or not away_team:
            return None
            
        try:
            home_score = int(home_team.get('score', 0))
            away_score = int(away_team.get('score', 0))
            
            # Check if winner is explicitly set
            if home_team.get('winner'):
                return home_team.get('team', {}).get('displayName')
            elif away_team.get('winner'):
                return away_team.get('team', {}).get('displayName')
            
            # Fallback to score comparison
            if home_score > away_score:
                return home_team.get('team', {}).get('displayName')
            elif away_score > home_score:
                return away_team.get('team', {}).get('displayName')
                
        except (ValueError, TypeError):
            pass
            
        return None

    @staticmethod
    def parse_game_data(event):
        """Parse game data from ESPN API event."""
        try:
            competition = event['competitions'][0]
            venue = competition.get('venue', {})
            
            # Get competitors
            home_team = next((team for team in competition['competitors'] if team['homeAway'] == 'home'), {})
            away_team = next((team for team in competition['competitors'] if team['homeAway'] == 'away'), {})
            
            # Get team data
            home_team_data = home_team.get('team', {})
            away_team_data = away_team.get('team', {})
            
            # Get scores
            try:
                home_score = int(home_team.get('score', 0))
                away_score = int(away_team.get('score', 0))
            except (ValueError, TypeError):
                home_score = 0
                away_score = 0
            
            # Get game status
            status = ESPNApiService.parse_game_status(event)
            
            # Get winner for final games
            winner = ESPNApiService.determine_winner(event)
            
            # Build game data
            try:
                # Parse the date string and ensure it's timezone aware
                date_str = event.get('date', '')
                logger.info(f"Raw date string from ESPN: {date_str}")
                
                if date_str:
                    # Add UTC timezone if not present
                    if not date_str.endswith('Z') and not '+' in date_str and not '-' in date_str:
                        date_str += 'Z'
                    game_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    logger.info(f"Parsed UTC game date: {game_date}")
                    
                    # Convert to Central Time for MNF detection
                    local_tz = tz.gettz('America/Chicago')
                    local_date = game_date.astimezone(local_tz)
                    logger.info(f"Local (CT) game date: {local_date}")
                else:
                    game_date = datetime.now(tz=tz.tzutc())
                    local_date = game_date.astimezone(tz.gettz('America/Chicago'))
                    logger.info(f"No date string found, using current time: {local_date}")

                # If the game date is more than 6 months in the future, it's probably a next season game
                # Adjust the year to the current year
                if (game_date - datetime.now(tz=tz.tzutc())).days > 180:
                    current_year = datetime.now().year
                    game_date = game_date.replace(year=current_year)
                    local_date = local_date.replace(year=current_year)
                    logger.info(f"Adjusted year to current year: {local_date}")
            
                is_monday = local_date.weekday() == 0  # Monday is 0
                is_evening = local_date.hour >= 18  # After 6 PM CT
                
                logger.info(f"Game day checks - Is Monday: {is_monday}, Is Evening: {is_evening}")
                
                # Enhanced MNF detection
                is_mnf = False
                if is_monday:
                    # Check various MNF indicators
                    name_indicators = [
                        'monday night football' in event.get('name', '').lower(),
                        'monday night' in event.get('name', '').lower(),
                        'mnf' in event.get('name', '').lower()
                    ]
                    
                    note_indicators = [
                        any('monday night' in note.get('headline', '').lower() 
                            for note in event.get('notes', [])),
                        any('mnf' in note.get('headline', '').lower() 
                            for note in event.get('notes', []))
                    ]
                    
                    broadcast_indicators = [
                        any('espn' in network.get('name', '').lower() 
                            for network in competition.get('broadcasts', [])),
                        any('monday night' in broadcast.get('name', '').lower() 
                            for broadcast in competition.get('broadcasts', []))
                    ]
                    
                    # Log all indicators
                    logger.info("MNF Detection Indicators:")
                    logger.info(f"  Game Name: {event.get('name', '')}")
                    logger.info(f"  Name Indicators: {name_indicators}")
                    logger.info(f"  Notes: {event.get('notes', [])}")
                    logger.info(f"  Note Indicators: {note_indicators}")
                    logger.info(f"  Broadcasts: {competition.get('broadcasts', [])}")
                    logger.info(f"  Broadcast Indicators: {broadcast_indicators}")
                    
                    # If it's Monday evening, it's likely MNF
                    if is_evening:
                        is_mnf = True
                        logger.info("Setting is_mnf=True because it's a Monday evening game")
                    # Or if we have other strong indicators
                    elif any(name_indicators) or any(note_indicators) or any(broadcast_indicators):
                        is_mnf = True
                        logger.info("Setting is_mnf=True because of name/note/broadcast indicators")
                    
                    logger.info(f"Final MNF Status: {is_mnf}")
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing game date: {e}")
                game_date = datetime.now(tz=tz.tzutc())
                local_date = game_date.astimezone(tz.gettz('America/Chicago'))
                is_mnf = False
            
            game_data = {
                'game_id': str(event['id']),
                'week': event.get('week', {}).get('number', 0),
                'season_type': event.get('season', {}).get('type', 2),
                'year': event.get('season', {}).get('year', datetime.now().year),
                'date': game_date.isoformat(),
                'status': status,
                'winning_team': winner,
                'home_team': {
                    'id': str(home_team_data.get('id', '')),
                    'display_name': home_team_data.get('displayName', ''),
                    'abbreviation': home_team_data.get('abbreviation', ''),
                    'score': home_score
                },
                'away_team': {
                    'id': str(away_team_data.get('id', '')),
                    'display_name': away_team_data.get('displayName', ''),
                    'abbreviation': away_team_data.get('abbreviation', ''),
                    'score': away_score
                },
                'venue': {
                    'name': venue.get('fullName', ''),
                    'city': venue.get('address', {}).get('city', ''),
                    'state': venue.get('address', {}).get('state', '')
                },
                'is_mnf': is_mnf,
                'game_time': local_date.strftime('%a %I:%M %p').replace(' 0', ' ')  # e.g., "Mon 7:15 PM"
            }
            
            logger.info(f"Parsed game data: {game_data}")
            return game_data
            
        except Exception as e:
            logger.error(f"Error parsing game data: {str(e)}")
            return {}

    @staticmethod
    def get_team_schedule(team_id: str, season_type: int = 2, year: Optional[int] = None) -> List[Dict]:
        """Get the full schedule for a specific team"""
        if not year:
            year = datetime.now().year
            
        try:
            try:
                response = requests.get(f"{ESPNApiService.BASE_URL}/teams/{team_id}/schedule", 
                                     timeout=10)  # 10 second timeout
                response.raise_for_status()  # Raise an error for bad status codes
                data = response.json()
            except requests.exceptions.Timeout:
                logger.error("ESPN API request timed out")
                return []
            except requests.exceptions.RequestException as e:
                logger.error(f"ESPN API request failed: {str(e)}")
                return []
            except ValueError as e:
                logger.error(f"Failed to parse ESPN API response as JSON: {str(e)}")
                return []
            
            games = []
            for event in data.get('events', []):
                if event.get('season', {}).get('type') != season_type:
                    continue
                    
                games.append({
                    'game_id': event.get('id'),
                    'name': event.get('name'),
                    'week': event.get('week', {}).get('number'),
                    'date': event.get('date')
                })
            
            return games
            
        except Exception as e:
            logger.error(f"Error fetching schedule for team {team_id}: {str(e)}")
            return []

    @staticmethod
    def get_mnf_game(week: int, season_type: int = 2, year: Optional[int] = None) -> Optional[Dict]:
        """Get the Monday Night Football game for a specific week"""
        games = ESPNApiService.get_week_games(week, season_type, year)
        
        for game in games:
            if game['is_mnf']:
                return game
        
        return None
